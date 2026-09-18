"""
BioReason mode-conditioned inference orchestrator.

Wires together: mode_router (decides WHAT kind of response is needed) +
mode_overlays (decides HOW the model should be instructed to respond) +
the actual model generation call. The orchestrator never determines
scientific content — it only frames the task before handing it to the
physical model (BR-VERIFIED-SFT-002 or whichever adapter is loaded).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .code_lint import extract_code_blocks, lint_generated_code
from .code_sandbox import run_in_sandbox
from .fixture_synth import build_execution_preamble, build_fixture_plan, infer_dataset_shape
from .mode_overlays import (
    audit_schema_ok,
    build_conditioned_system_prompt,
    max_new_tokens_for_mode,
)
from .mode_router import RouterDecision, decide_mode

GenerateFn = Callable[[List[Dict[str, str]], int], str]


@dataclass
class OrchestratedTurn:
    user_message: str
    router: RouterDecision
    system_prompt_used: str
    response: str
    response_source: str
    audit_regeneration_used: bool
    latency_seconds: float
    code_lint_warnings: List[str] = field(default_factory=list)
    code_lint_regeneration_used: bool = False
    execution_verified: Optional[bool] = None
    execution_error: Optional[str] = None
    execution_regeneration_used: bool = False


def run_orchestrated_turn(
    generate_fn: GenerateFn,
    history: List[Dict[str, str]],
    user_message: str,
    pipeline_context_summary: Optional[str] = None,
    main_max_new_tokens: int = 400,
    router_max_new_tokens: int = 60,
    enable_two_pass_audit: bool = True,
    enable_execution_verification: bool = True,
) -> OrchestratedTurn:
    import tempfile
    import time
    from pathlib import Path

    t0 = time.time()
    router = decide_mode(
        generate_fn=generate_fn,
        history=history,
        user_message=user_message,
        pipeline_context_summary=pipeline_context_summary,
        max_new_tokens=router_max_new_tokens,
    )

    system_prompt = build_conditioned_system_prompt(router.mode)
    if router.explicit_user_request and "json" in user_message.lower():
        system_prompt += " The user explicitly asked for JSON output — return raw JSON in this case."

    # Code-generation and structured-audit modes need more headroom than a
    # plain conversational reply gets by default; never shrink a caller-
    # specified budget, only raise it when the mode needs more.
    effective_max_new_tokens = max(main_max_new_tokens, max_new_tokens_for_mode(router.mode))

    main_messages = [{"role": "system", "content": system_prompt}] + history + [
        {"role": "user", "content": user_message}
    ]
    response = generate_fn(main_messages, effective_max_new_tokens)

    audit_regeneration_used = False
    if router.mode == "SCIENTIFIC_AUDIT" and enable_two_pass_audit and not audit_schema_ok(response):
        reformat_messages = [
            {
                "role": "system",
                "content": (
                    system_prompt
                    + " Reformat your previous answer into the structured audit sections "
                    "described above. Preserve the scientific content exactly — reorganize, "
                    "do not invent new claims."
                ),
            },
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response},
            {"role": "user", "content": "Please reformat that as a structured audit."},
        ]
        reformatted = generate_fn(reformat_messages, effective_max_new_tokens)
        if reformatted.strip():
            response = reformatted
            audit_regeneration_used = True

    # Static code review for generated pipeline code: live testing found
    # BR-VERIFIED-SFT-002 repeatedly generates PIPELINE_BUILD code that
    # reads correctly (right library, right variable names, comments
    # describing the right operation) but is structurally broken -- calling
    # methods that don't exist on the object in question, referencing
    # columns never computed, or claiming an aggregation it doesn't
    # actually perform. Prompt-engineering alone could not reliably prevent
    # this, so this is a deterministic check (see code_lint.py) with one
    # corrective regeneration attempt, falling back to an honest caveat
    # appended to the response if the issue isn't resolved -- never silently
    # shipping code the review found suspect.
    # PIPELINE_DEBUG also generates/rewrites code (a proposed fix for a
    # reported bug), so it needs the same review -- live testing found a
    # PIPELINE_DEBUG "fix" that correctly diagnosed the root cause but
    # proposed a replacement that had the identical class of bug in a
    # different form.
    code_lint_warnings: List[str] = []
    code_lint_regeneration_used = False
    if router.mode in ("PIPELINE_BUILD", "PIPELINE_DEBUG"):
        code_lint_warnings = lint_generated_code(response)
        if code_lint_warnings:
            fix_messages = [{"role": "system", "content": system_prompt}] + history + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": response},
                {
                    "role": "user",
                    "content": (
                        "A static code review found these specific problems in that "
                        "code:\n" + "\n".join(f"- {w}" for w in code_lint_warnings) + "\n"
                        "Please rewrite the code to fix these exact issues. Keep "
                        "everything else the same."
                    ),
                },
            ]
            corrected = generate_fn(fix_messages, effective_max_new_tokens)
            if corrected.strip():
                remaining = lint_generated_code(corrected)
                if len(remaining) < len(code_lint_warnings):
                    response = corrected
                    code_lint_warnings = remaining
                    code_lint_regeneration_used = True
        if code_lint_warnings:
            response += (
                "\n\n---\n**Automated review found unresolved issues in this code — "
                "verify before running:**\n"
                + "\n".join(f"- {w}" for w in code_lint_warnings)
            )

    # Execution-in-the-loop verification: code_lint above catches known
    # failure patterns cheaply, but it's reactive -- only bugs someone
    # already saw and hand-encoded as a regex. This stage actually RUNS the
    # generated code against a small synthetic dataset (see fixture_synth.py)
    # and catches whatever real exception occurs, known pattern or not.
    # BioReason never has the user's real data, so this proves the code
    # runs without crashing on something structurally similar -- never
    # scientific correctness on the user's actual dataset. If the code's
    # file I/O can't be safely fixtured (fixture_synth.build_fixture_plan
    # returns confidence="none"), execution is skipped silently, not
    # flagged -- a false-positive execution failure would be worse than the
    # static linter it complements, since "the code was actually run" reads
    # as more authoritative than a heuristic warning.
    # PIPELINE_DEBUG gets the same check as PIPELINE_BUILD (mirrors the
    # code_lint gate above): a proposed debug fix is still generated code
    # that can be wrong in a new way -- live testing found exactly this,
    # a PIPELINE_DEBUG "fix" that correctly diagnosed the root cause but
    # introduced a different bug, which only real execution caught.
    execution_verified: Optional[bool] = None
    execution_error: Optional[str] = None
    execution_regeneration_used = False
    if router.mode in ("PIPELINE_BUILD", "PIPELINE_DEBUG") and enable_execution_verification:
        shape = infer_dataset_shape(user_message, history, pipeline_context_summary)

        def _try_execute(text: str):
            blocks = extract_code_blocks(text)
            if not blocks:
                return None
            plan = build_fixture_plan(blocks[0], shape)
            if plan.confidence == "none":
                return None
            preamble = build_execution_preamble(plan)
            full_source = preamble + "\n\n" + blocks[0]
            with tempfile.TemporaryDirectory() as workdir:
                return run_in_sandbox(full_source, Path(workdir))

        result = _try_execute(response)
        if result is not None:
            if result.status == "OK":
                execution_verified = True
            elif result.status == "EXCEPTION":
                fix_messages = [{"role": "system", "content": system_prompt}] + history + [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": response},
                    {
                        "role": "user",
                        "content": (
                            "Running this code in a controlled test environment "
                            "(synthetic data, or mocked external tool calls for "
                            "shell-orchestration code) raised a real error:\n```\n"
                            + (result.traceback_text or "") + "\n```\n"
                            "Please rewrite the code to fix this exact error. Keep "
                            "everything else the same."
                        ),
                    },
                ]
                corrected = generate_fn(fix_messages, effective_max_new_tokens)
                if corrected.strip():
                    reresult = _try_execute(corrected)
                    if reresult is not None and reresult.status == "OK":
                        response = corrected
                        execution_verified = True
                        execution_regeneration_used = True
                    else:
                        execution_verified = False
                        execution_error = result.traceback_text
                else:
                    execution_verified = False
                    execution_error = result.traceback_text
            # TIMEOUT / RESOURCE_LIMIT / ENVIRONMENT_ERROR are all treated
            # as inconclusive, not a code bug -- execution_verified stays
            # None. ENVIRONMENT_ERROR specifically (an ImportError/
            # ModuleNotFoundError from a missing or conflicting dependency
            # in the execution environment) is never something the model
            # can fix by rewriting its logic, so it's never worth a
            # corrective regeneration attempt or a caveat that would
            # misleadingly read as a problem with the user's pipeline.

        if execution_verified is False:
            response += (
                "\n\n---\n**Execution in a controlled test environment (synthetic "
                "data, or mocked external tool calls for shell-orchestration code) "
                "failed with a real error (not a heuristic warning):**\n```\n"
                + (execution_error or "unknown error") + "\n```"
            )

    latency = time.time() - t0
    return OrchestratedTurn(
        user_message=user_message,
        router=router,
        system_prompt_used=system_prompt,
        response=response,
        response_source="MODEL_GENERATED",
        audit_regeneration_used=audit_regeneration_used,
        latency_seconds=latency,
        code_lint_warnings=code_lint_warnings,
        code_lint_regeneration_used=code_lint_regeneration_used,
        execution_verified=execution_verified,
        execution_error=execution_error,
        execution_regeneration_used=execution_regeneration_used,
    )

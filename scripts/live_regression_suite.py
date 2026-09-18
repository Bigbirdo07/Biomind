"""
scripts/live_regression_suite.py

Replays the concrete scenarios found and fixed during live testing of
BR-VERIFIED-SFT-002's mode-conditioned inference (router broadening,
PIPELINE_INTAKE overlay rewrite, PIPELINE_BUILD/PIPELINE_DEBUG code-lint
pass) against a running serve_verified_model.py instance, so future
overlay/router/lint changes can be checked against everything already
fixed instead of relying on someone remembering to retest by hand.

Two tiers of checks, because live model output has real sampling
variance:

  HARD checks -- invariants the ORCHESTRATOR CODE guarantees regardless of
  what the model says (e.g. "if code_lint found warnings, those exact
  warnings appear in the response text" -- this is a deterministic
  property of run_orchestrated_turn, not something the model can get
  right or wrong). A HARD failure means the code itself regressed.

  SOFT checks -- expectations about model BEHAVIOR (e.g. "router
  classifies this as PIPELINE_INTAKE", "this known-good code pattern
  produces zero lint warnings"). These can occasionally fail from normal
  LLM sampling variance without indicating a real regression -- they are
  reported for human review, not treated as a build-breaking failure.

Usage:
    python3 scripts/live_regression_suite.py [--url http://localhost:8099]
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

Check = Callable[[Dict[str, Any]], Tuple[bool, str]]


@dataclass
class Scenario:
    name: str
    history: List[Dict[str, str]]
    user_message: str
    hard_checks: List[Tuple[str, Check]] = field(default_factory=list)
    soft_checks: List[Tuple[str, Check]] = field(default_factory=list)


def call_generate(base_url: str, history: List[Dict[str, str]], user_message: str) -> Dict[str, Any]:
    body = json.dumps({"history": history, "user_message": user_message}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/generate", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# Reusable hard checks -- these hold regardless of what the model produces.
# ---------------------------------------------------------------------------

def hard_lint_honesty_invariant(result: Dict[str, Any]) -> Tuple[bool, str]:
    """If code_lint_warnings is non-empty, the orchestrator guarantees those
    exact warnings are appended to the response text. This is a property of
    orchestrator.py's own code, not the model -- any failure here means the
    code_lint-to-response wiring itself broke."""
    warnings = result.get("code_lint_warnings") or []
    if not warnings:
        return True, "no warnings to check"
    text = result.get("text", "")
    missing = [w for w in warnings if w not in text]
    if missing:
        return False, f"{len(missing)} lint warning(s) NOT reflected in response text: {missing}"
    return True, f"{len(warnings)} warning(s) correctly surfaced in response text"


def hard_response_source(result: Dict[str, Any]) -> Tuple[bool, str]:
    ok = result.get("response_source") == "MODEL_GENERATED"
    return ok, f"response_source={result.get('response_source')}"


def hard_execution_honesty_invariant(result: Dict[str, Any]) -> Tuple[bool, str]:
    """If execution_verified is explicitly False, the orchestrator
    guarantees the real observed traceback (execution_error) is appended
    to the response text -- same honesty-invariant property as
    hard_lint_honesty_invariant, for the execution-in-the-loop stage. A
    failure here means the code_sandbox-to-response wiring itself broke,
    not a model behavior issue."""
    if result.get("execution_verified") is not False:
        return True, f"execution_verified={result.get('execution_verified')}, nothing to check"
    error = result.get("execution_error") or ""
    text = result.get("text", "")
    if not error:
        return False, "execution_verified=False but execution_error is empty"
    if error not in text:
        return False, "execution_error not reflected verbatim in response text"
    return True, "execution_error correctly surfaced in response text"


def hard_valid_router_mode(result: Dict[str, Any]) -> Tuple[bool, str]:
    from bioreason.inference.mode_router import VALID_MODES
    mode = result.get("router_mode")
    ok = mode in VALID_MODES
    return ok, f"router_mode={mode}"


def soft_router_mode_is(expected: str) -> Check:
    def check(result: Dict[str, Any]) -> Tuple[bool, str]:
        actual = result.get("router_mode")
        return actual == expected, f"expected {expected}, got {actual}"
    return check


def soft_no_lint_warnings(result: Dict[str, Any]) -> Tuple[bool, str]:
    warnings = result.get("code_lint_warnings") or []
    return not warnings, f"{len(warnings)} warning(s): {warnings}" if warnings else "clean"


def soft_text_contains(substring: str) -> Check:
    def check(result: Dict[str, Any]) -> Tuple[bool, str]:
        text = result.get("text", "")
        ok = substring.lower() in text.lower()
        return ok, f"looked for {substring!r}"
    return check


def soft_text_not_contains(substring: str) -> Check:
    def check(result: Dict[str, Any]) -> Tuple[bool, str]:
        text = result.get("text", "")
        ok = substring.lower() not in text.lower()
        return ok, f"should not contain {substring!r}"
    return check


# ---------------------------------------------------------------------------
# Scenarios -- each one is a bug found and fixed during live testing this
# session. See conversation history / mode_overlays.py comments for the
# original broken output each one is guarding against.
# ---------------------------------------------------------------------------

SCENARIOS: List[Scenario] = [
    Scenario(
        name="router: vague data statement routes to PIPELINE_INTAKE, not GENERAL_CHAT",
        history=[],
        user_message="I have this dataset I am working with and I want to do something with it.",
        soft_checks=[("mode", soft_router_mode_is("PIPELINE_INTAKE"))],
    ),
    Scenario(
        name="router: pure greeting stays GENERAL_CHAT",
        history=[],
        user_message="hi, what can you help me with?",
        soft_checks=[("mode", soft_router_mode_is("GENERAL_CHAT"))],
    ),
    Scenario(
        name="router: concept question stays TEACHING",
        history=[],
        user_message="what is PCA and why do people use it in RNA-seq?",
        soft_checks=[("mode", soft_router_mode_is("TEACHING"))],
    ),
    Scenario(
        name="router: implicit scenario without audit language stays SCIENTIFIC_REASONING",
        history=[],
        user_message=(
            "I used the same 20 mice for both my discovery cohort and my "
            "validation cohort in this RNA-seq study, is that a problem?"
        ),
        soft_checks=[("mode", soft_router_mode_is("SCIENTIFIC_REASONING"))],
    ),
    Scenario(
        name="intake: single-cell nested-in-subject design gets pseudoreplication flagged",
        history=[
            {"role": "user", "content": (
                "I study transmissible cancer in soft-shell clams. I want to know "
                "which genes distinguish neoplastic hemocytes from healthy hemocytes "
                "over disease progression. I ran single-cell RNA-seq and have "
                "filtered_feature_bc_matrix.h5 files for 4 healthy and 6 neoplastic "
                "animals at three disease stages."
            )},
            {"role": "assistant", "content": (
                "So the goal is to find which genes distinguish neoplastic from "
                "normal hemocytes over the disease time course. You mentioned "
                "filtered_feature_bc_matrix.h5 files, already processed. Do you "
                "have any specific hypotheses, or exploratory? Also any batch "
                "effect concerns?"
            )},
        ],
        user_message=(
            "Exploratory, no batch concerns, all sequenced in one run. I just "
            "want to run differential expression comparing neoplastic vs healthy cells."
        ),
        soft_checks=[
            ("mentions pseudoreplication/aggregation risk", soft_text_contains("pseudobulk")),
        ],
    ),
    Scenario(
        name="intake: ordinary paired bulk design does NOT get a false nesting flag",
        history=[],
        user_message=(
            "I want to find genes that cause brain cancer. Bulk RNA-seq, filtered "
            "count matrix, 15 tumor and 15 matched normal samples from the same "
            "patients, raw counts, no batch effects."
        ),
        soft_checks=[
            ("mode", soft_router_mode_is("PIPELINE_INTAKE")),
            ("does not fabricate pseudoreplication concern", soft_text_not_contains("pseudoreplication")),
        ],
    ),
    Scenario(
        name="build: single-cell pseudobulk DE code (the 4x-broken scenario)",
        history=[
            {"role": "user", "content": (
                "I study transmissible cancer in soft-shell clams. I want to know "
                "which genes distinguish neoplastic hemocytes from healthy hemocytes "
                "over disease progression. I ran single-cell RNA-seq and have "
                "filtered_feature_bc_matrix.h5 files for 4 healthy and 6 neoplastic "
                "animals at three disease stages."
            )},
            {"role": "assistant", "content": (
                "So the goal is to find which genes distinguish neoplastic from "
                "normal hemocytes over the disease time course. You mentioned "
                "filtered_feature_bc_matrix.h5 files, already processed. Do you "
                "have any specific hypotheses, or exploratory? Also any batch "
                "effect concerns?"
            )},
            {"role": "user", "content": (
                "Exploratory, no batch concerns, all sequenced in one run. I just "
                "want to run differential expression comparing neoplastic vs healthy cells."
            )},
            {"role": "assistant", "content": (
                "Great, with exploratory goals and no batch concerns, we can "
                "proceed straightforwardly. We will aggregate cells by animal to "
                "avoid pseudoreplication, then compare neoplastic vs healthy cells "
                "across disease stages using pseudobulk DE."
            )},
        ],
        user_message="Yes, let's use Scanpy for the pseudobulk aggregation and DESeq2-style DE. Please give me the code.",
        hard_checks=[
            ("lint honesty invariant", hard_lint_honesty_invariant),
            ("execution honesty invariant", hard_execution_honesty_invariant),
            ("response_source", hard_response_source),
        ],
        soft_checks=[
            ("mode", soft_router_mode_is("PIPELINE_BUILD")),
            ("no lint warnings (library-function pattern used)", soft_no_lint_warnings),
        ],
    ),
    Scenario(
        name="build: paired bulk RNA-seq DESeq2 code stays clean",
        history=[
            {"role": "user", "content": (
                "Bulk RNA-seq, filtered count matrix, 15 tumor and 15 matched "
                "normal samples from the same patients, raw counts, no batch "
                "effects. Goal: find genes that cause brain cancer."
            )},
            {"role": "assistant", "content": (
                "Paired differential expression with DESeq2 is the right "
                "approach given matched samples from the same patients."
            )},
        ],
        user_message="Give me the code for this.",
        hard_checks=[
            ("lint honesty invariant", hard_lint_honesty_invariant),
            ("execution honesty invariant", hard_execution_honesty_invariant),
        ],
        soft_checks=[
            ("mode", soft_router_mode_is("PIPELINE_BUILD")),
            ("no lint warnings", soft_no_lint_warnings),
        ],
    ),
    Scenario(
        name="build: single-cell QC + UMAP code sets seeds and computes before plotting",
        history=[],
        user_message=(
            "I have single-cell RNA-seq data, 6 tumor and 6 healthy mouse samples, "
            "filtered_feature_bc_matrix.h5 per sample, metadata.csv with "
            "animal/condition/file_path columns. Give me code for QC, PCA, and "
            "Leiden clustering with UMAP visualization."
        ),
        hard_checks=[
            ("lint honesty invariant", hard_lint_honesty_invariant),
            ("execution honesty invariant", hard_execution_honesty_invariant),
        ],
        soft_checks=[
            ("mode", soft_router_mode_is("PIPELINE_BUILD")),
            ("sets random_state for reproducibility", soft_text_contains("random_state")),
            ("no lint warnings", soft_no_lint_warnings),
        ],
    ),
    Scenario(
        name="debug: AnnData .groupby() AttributeError gets diagnosed and lint-reviewed",
        history=[
            {"role": "user", "content": (
                "Here is my pseudobulk aggregation code:\n```python\n"
                "pseudobulk_adata = sc.AnnData()\n"
                "pseudobulk_adata = pseudobulk_adata.concatenate(adata)\n"
                "pseudobulk_adata = pseudobulk_adata.groupby('animal').mean()\n```"
            )},
            {"role": "assistant", "content": "That code aggregates cells by animal to create pseudobulk profiles."},
        ],
        user_message="I ran this and got: AttributeError: 'AnnData' object has no attribute 'groupby'. What is wrong?",
        hard_checks=[
            ("lint honesty invariant", hard_lint_honesty_invariant),
            ("execution honesty invariant", hard_execution_honesty_invariant),
        ],
        soft_checks=[
            ("mode", soft_router_mode_is("PIPELINE_DEBUG")),
            ("correctly diagnoses AnnData has no groupby", soft_text_contains("groupby")),
        ],
    ),
    Scenario(
        name="reasoning: DE result interpretation avoids overclaiming causation",
        history=[
            {"role": "user", "content": (
                "I compared tumor vs normal brain tissue with paired bulk RNA-seq, "
                "15 patients, DESeq2. Got 340 significantly differentially "
                "expressed genes (padj < 0.05, |log2FC| > 1). Top upregulated "
                "genes are EGFR, VEGFA, MKI67."
            )},
            {"role": "assistant", "content": (
                "That is a substantial set of differentially expressed genes with "
                "well-known cancer-associated genes among the top hits."
            )},
        ],
        user_message="What does this mean? What should I do next?",
        soft_checks=[
            ("does not overclaim direct causation", soft_text_not_contains("these genes cause")),
            ("gives a concrete next step", soft_text_contains("valid")),
        ],
    ),
]


def run_suite(base_url: str) -> int:
    hard_failures = 0
    soft_failures = 0
    for scenario in SCENARIOS:
        print(f"\n=== {scenario.name} ===")
        try:
            result = call_generate(base_url, scenario.history, scenario.user_message)
        except Exception as exc:
            print(f"  [ERROR] request failed: {exc}")
            hard_failures += 1
            continue

        for check_name, check_fn in scenario.hard_checks:
            ok, detail = check_fn(result)
            status = "PASS" if ok else "FAIL (HARD)"
            print(f"  [{status}] {check_name}: {detail}")
            if not ok:
                hard_failures += 1

        for check_name, check_fn in scenario.soft_checks:
            ok, detail = check_fn(result)
            status = "PASS" if ok else "WARN (soft)"
            print(f"  [{status}] {check_name}: {detail}")
            if not ok:
                soft_failures += 1

    print(f"\n{'=' * 60}")
    print(f"HARD failures (real regressions, code-level): {hard_failures}")
    print(f"SOFT failures (model-behavior, review manually): {soft_failures}")
    print(f"{'=' * 60}")
    return 1 if hard_failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8099")
    args = parser.parse_args()
    sys.exit(run_suite(args.url))

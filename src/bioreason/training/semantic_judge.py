"""
Semantic (LLM-judge) scorer for BioReason Dev/Regression predictions.

v2: two-step, reference-blind judging. v1 (single-step, judge sees both the
reference answer and the response in the same prompt) was found to leak
reference details into the judge's justification even when the response
itself never stated them — e.g. crediting a response that only said
"data_leakage" as correctly identifying "correlated scans from the same
patient" because the judge could see that phrase in the reference material,
not because the response said it. v2 fixes this by splitting into two
model calls:

  Step 1 (EXTRACT, blind to the reference): given only the scenario/question
  and the response, ask the model to summarize what mechanism/issue the
  response itself claims — it cannot see the reference, so it cannot
  "helpfully" fill in details the response didn't actually say.

  Step 2 (COMPARE): given the Step-1 extraction (not the raw response) and
  the reference (flaw_type, rationale, key_points), judge whether the
  extracted claim matches. The comparison step never sees the original
  response text, only what was actually extracted from it.

Lives under bioreason.training (not bioreason.evaluation) deliberately: the
evaluation package's __init__ pulls in bioreason.schemas, which requires
pydantic — not installed in the Unity training conda env used to run
verified inference/eval jobs. bioreason.training has no such dependency.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

EXTRACT_INSTRUCTION = (
    "You will be given a research scenario/question and a model's response "
    "to it. Do NOT judge correctness. Only summarize, in one or two "
    "sentences, what specific mechanism or issue (if any) the response "
    "itself claims is the problem — using only what the response actually "
    "says, not what you think the answer should be. If the response "
    "concludes the design is valid with no flaw, say that. If the response "
    "only names a generic category (e.g. 'data leakage') without "
    "explaining the specific mechanism, say exactly that — do not fill in "
    "specifics the response didn't state.\n\n"
    "Respond with ONLY a single JSON object, no other text:\n"
    '{"claimed_valid": <true|false>, "claimed_mechanism_summary": "<your summary, '
    'or empty string if claimed_valid is true>", "is_generic_label_only": <true|false>}'
)

COMPARE_INSTRUCTION = (
    "You are a strict but fair scientific grader. You will be given whether "
    "a scenario actually contains a flaw, the expected mechanism (if any), "
    "and a SUMMARY of what a model's response claimed (already extracted — "
    "you are not seeing the original response). Judge whether the claimed "
    "mechanism matches the expected one. Different terminology is fine as "
    "long as the underlying mechanism is the same. A generic category label "
    "with no specific mechanism (e.g. just 'data leakage' with no "
    "explanation of what leaks or why) should be judged INCORRECT even if "
    "the category is technically right — we require the specific mechanism, "
    "not just the right bucket. For valid/unflawed scenarios, the response "
    "should correctly claim validity, not invent a flaw.\n\n"
    "Respond with ONLY a single JSON object, no other text:\n"
    '{"correct": <true|false>, "confidence": <0.0-1.0>, "justification": "<one sentence>"}'
)


def build_extract_prompt(scenario: str, question: str, prediction: str) -> str:
    return (
        f"Scenario:\n{scenario}\n\n"
        f"Question:\n{question}\n\n"
        f"Response to summarize:\n{prediction}\n\n"
        "Summarize only what this response itself claims."
    )


def build_compare_prompt(
    flawed: bool,
    flaw_type: Optional[str],
    ground_truth_rationale: Optional[str],
    key_points: Optional[list],
    claimed_valid: bool,
    claimed_mechanism_summary: str,
    is_generic_label_only: bool,
) -> str:
    if flawed:
        expected = (
            f"This scenario DOES contain a flaw. Expected mechanism: {flaw_type or 'unspecified'}.\n"
            f"Reference rationale: {ground_truth_rationale or '(none provided)'}\n"
            f"Reference key points (for context only, response need not use these exact words): "
            f"{', '.join(key_points) if key_points else '(none)'}"
        )
    else:
        expected = "This scenario is methodologically VALID — there is no flaw to detect."

    claim = (
        "The response claimed the design is VALID (no flaw)."
        if claimed_valid
        else f"The response's claimed mechanism (extracted, generic-label-only={is_generic_label_only}): {claimed_mechanism_summary}"
    )

    return f"{expected}\n\n{claim}\n\nIs the response's claim correct?"


def parse_json_object(text: str) -> Optional[Dict[str, Any]]:
    match = re.search(r"\{.*\}", text.strip(), re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def parse_extract_output(text: str) -> Optional[Dict[str, Any]]:
    obj = parse_json_object(text)
    if obj is None or "claimed_valid" not in obj:
        return None
    obj.setdefault("claimed_mechanism_summary", "")
    obj.setdefault("is_generic_label_only", False)
    return obj


def parse_compare_output(text: str) -> Optional[Dict[str, Any]]:
    obj = parse_json_object(text)
    if obj is None or not isinstance(obj.get("correct"), bool):
        return None
    return obj

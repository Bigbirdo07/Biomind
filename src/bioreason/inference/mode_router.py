"""
BioReason Mode Router — inference-time response-mode classification.

This is NOT keyword matching (see bioreason.pipeline.intent.PipelineIntentClassifier
for that legacy heuristic, kept only as a last-resort fallback). The router
issues a real, short classification generation to the SAME physical model
(BR-VERIFIED-SFT-002, or whichever model/adapter is loaded) asking it to
return a structured JSON mode decision, given the actual conversation
history and any active PipelineContext. It does not perform scientific
reasoning — it only decides which response mode/overlay to apply before the
real answer is generated.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

VALID_MODES = [
    "GENERAL_CHAT",
    "TEACHING",
    "SCIENTIFIC_REASONING",
    "SCIENTIFIC_AUDIT",
    "PIPELINE_INTAKE",
    "PIPELINE_BUILD",
    "PIPELINE_DEBUG",
    "CODE_EXPLANATION",
    "INSUFFICIENT_INFORMATION",
]

ROUTER_INSTRUCTION = (
    "You are a response-mode classifier for a scientific assistant. Given the "
    "conversation so far and the latest user message, decide which response "
    "mode is appropriate. Do not answer the user's question. Do not perform "
    "scientific analysis. Only classify.\n\n"
    "Valid modes:\n"
    "- GENERAL_CHAT: greetings, small talk, capability questions\n"
    "- TEACHING: user is asking what a concept/term means, in general\n"
    "- SCIENTIFIC_REASONING: user describes a specific scenario and implicitly "
    "wants to know if it's valid, without explicitly asking for a formal audit\n"
    "- SCIENTIFIC_AUDIT: user explicitly asks for an audit, review, methodological "
    "assessment, or structured critique of a design\n"
    "- PIPELINE_INTAKE: user has data, an experiment, or a dataset they want "
    "help analyzing, comparing, or building a pipeline/workflow for -- "
    "*even if they never say the word 'pipeline'* -- but the research "
    "question, assay type, data stage, or comparison is not yet established "
    "in this conversation. Vague statements like 'I have this dataset and "
    "want to do something with it' or 'I did some sequencing on my samples' "
    "belong here, not GENERAL_CHAT -- the user has real data/analysis "
    "intent, they just haven't been asked the right questions yet\n"
    "- PIPELINE_BUILD: user wants code/pipeline generation and enough experimental "
    "detail is already known from this conversation\n"
    "- PIPELINE_DEBUG: user reports an error, exception, traceback, or "
    "something broken/not working, in the context of a pipeline -- this "
    "applies EVEN IF the user also pastes the code that produced the error, "
    "and even if their question is phrased as \"what is wrong\" or \"what "
    "does this mean\" rather than \"fix this\". The presence of a reported "
    "error or traceback is what matters, not the exact phrasing of the "
    "question\n"
    "- CODE_EXPLANATION: user asks what a piece of code does or how it maps "
    "to a computational/biological concept, with NO reported error, "
    "exception, or traceback anywhere in their message -- if the user "
    "pasted an error message or traceback, it is PIPELINE_DEBUG, never "
    "CODE_EXPLANATION, regardless of how the question is phrased\n"
    "- INSUFFICIENT_INFORMATION: user asks for a judgment (e.g. 'is my analysis valid') "
    "but has given no scenario/design details at all\n\n"
    "The most common mistake is over-classifying SCIENTIFIC_REASONING as "
    "SCIENTIFIC_AUDIT. The deciding question is: did the user use audit/review/"
    "assess/critique language, or explicitly ask for a structured assessment? "
    "If not — even if the scenario clearly has a methodological problem — it is "
    "SCIENTIFIC_REASONING, not SCIENTIFIC_AUDIT. Examples:\n"
    "- \"I have 10 patients with four biopsies each and randomly split the 40 "
    "biopsies across train and test. Is that okay?\" -> SCIENTIFIC_REASONING "
    "(scenario + implicit question, no audit language)\n"
    "- \"I used the same 20 mice for both the discovery cohort and the "
    "validation cohort.\" -> SCIENTIFIC_REASONING (statement + implicit "
    "question, no audit language)\n"
    "- \"I ran 5,000 statistical tests and didn't apply any multiple-testing "
    "correction.\" -> SCIENTIFIC_REASONING (no audit language)\n"
    "- \"Audit this experimental design: 15 tumor and 15 normal samples, "
    "batch confounded with group.\" -> SCIENTIFIC_AUDIT (explicit \"audit\")\n"
    "- \"Please review this pipeline for leakage.\" -> SCIENTIFIC_AUDIT "
    "(explicit \"review\")\n"
    "- \"Perform a methodological audit of this RNA-seq study.\" -> "
    "SCIENTIFIC_AUDIT (explicit \"audit\")\n"
    "- \"I have this dataset I'm working with and I want to do something "
    "with it.\" -> PIPELINE_INTAKE (real data + analysis intent, no "
    "research question or assay type established yet -- NOT GENERAL_CHAT, "
    "even though the word 'pipeline' was never used)\n"
    "- \"I did some sequencing on my samples and want to figure out what's "
    "going on.\" -> PIPELINE_INTAKE (same reasoning)\n"
    "- \"hi, what can you help me with?\" -> GENERAL_CHAT (no data/analysis "
    "intent at all, pure greeting/capability question)\n\n"
    "A second common mistake is under-classifying a fully-specified request as "
    "PIPELINE_INTAKE out of caution, when it is actually PIPELINE_BUILD. If the "
    "user's message already states the assay/data type, the sample design, the "
    "research question, AND an explicit request to build/generate the pipeline "
    "or code, that is PIPELINE_BUILD -- do not downgrade it to PIPELINE_INTAKE "
    "just because it would feel more thorough to ask a confirming question "
    "first. Asking to confirm before building is not appropriate here; the "
    "user has already given enough to build. Example:\n"
    "- \"I have whole genome sequencing on 12 tumor samples and 12 matched "
    "normal samples from the same patients. Raw fastq files. I want to find "
    "somatic mutations driving the cancer, and I want to build the full "
    "pipeline.\" -> PIPELINE_BUILD (assay=WGS, data stage=raw fastq, design="
    "paired tumor/normal with sample counts, research question=somatic "
    "mutation discovery, AND an explicit build request are all present -- "
    "everything PIPELINE_BUILD requires is already established, so build it "
    "rather than asking the user to re-confirm what they already said)\n\n"
    "Do not over-apply this: stating a research goal (e.g. \"I want to find "
    "genes/mutations/variants that do X\") is normal in almost every message "
    "and is NOT by itself a build request -- it is just the research question "
    "part of the four requirements above. All four (assay/data type, sample "
    "design, research question, AND a separate explicit ask to build/generate "
    "the pipeline/code) must be present for PIPELINE_BUILD. If the explicit "
    "build/generate ask is missing, stay in PIPELINE_INTAKE even when the "
    "design is fully specified. Contrast:\n"
    "- \"I want to find genes that cause brain cancer. Bulk RNA-seq, filtered "
    "count matrix, 15 tumor and 15 matched normal samples from the same "
    "patients, raw counts, no batch effects.\" -> PIPELINE_INTAKE (assay, data "
    "stage, design, and research question are all present, but there is no "
    "explicit request to build/generate a pipeline or code -- do not build "
    "unprompted just because the design is complete)\n"
    "- Same message plus \", and I want you to build the pipeline for this\" "
    "-> PIPELINE_BUILD (now the explicit build request is present too)\n\n"
    "A third common mistake is misclassifying PIPELINE_DEBUG as "
    "CODE_EXPLANATION when the user pastes code together with an error. "
    "Examples:\n"
    "- \"Here is my code: [code]. I ran this and got: AttributeError: "
    "'AnnData' object has no attribute 'groupby'. What is wrong?\" -> "
    "PIPELINE_DEBUG (a real error/traceback was reported -- 'what is "
    "wrong' is still a debug question, not a request to explain the code's "
    "general purpose)\n"
    "- \"Here is my code: [code]. What does this do?\" -> CODE_EXPLANATION "
    "(no error reported anywhere, purely asking what the code accomplishes)\n"
    "- \"Why did you use PCA here?\" -> CODE_EXPLANATION (no error, asking "
    "for the rationale behind a design choice already in the code)\n\n"
    "A short follow-up (e.g. 'why?', 'show me', 'make that structured') should be "
    "classified using the conversation history, not in isolation.\n\n"
    "Respond with ONLY a single JSON object, no other text, in exactly this shape:\n"
    '{"mode": "<ONE_OF_THE_MODES_ABOVE>", "confidence": <0.0-1.0>, '
    '"explicit_user_request": <true|false>}\n\n'
    "\"explicit_user_request\" is true only if the user's own words explicitly "
    "named the mode/format they want (e.g. said 'audit', 'as JSON', 'just the code')."
)


@dataclass
class RouterDecision:
    mode: str
    confidence: float
    explicit_user_request: bool
    raw_output: str
    parse_ok: bool
    fallback_used: bool = False


def build_router_messages(
    history: List[Dict[str, str]],
    user_message: str,
    pipeline_context_summary: Optional[str] = None,
) -> List[Dict[str, str]]:
    convo_lines = []
    for turn in history[-6:]:  # bounded context window
        role = "User" if turn["role"] == "user" else "Assistant"
        convo_lines.append(f"{role}: {turn['content']}")
    convo_text = "\n".join(convo_lines) if convo_lines else "(no prior turns)"
    pipeline_text = pipeline_context_summary or "(no active pipeline context)"
    user_prompt = (
        f"Conversation so far:\n{convo_text}\n\n"
        f"Active pipeline context: {pipeline_text}\n\n"
        f"Latest user message: {user_message}"
    )
    return [
        {"role": "system", "content": ROUTER_INSTRUCTION},
        {"role": "user", "content": user_prompt},
    ]


def parse_router_output(text: str) -> Optional[Dict[str, Any]]:
    stripped = text.strip()
    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if not match:
        return None
    try:
        obj = json.loads(match.group(0))
    except Exception:
        return None
    if obj.get("mode") not in VALID_MODES:
        return None
    if not isinstance(obj.get("confidence"), (int, float)):
        return None
    return obj


def keyword_fallback_mode(user_message: str) -> str:
    """Last-resort fallback only, used when the model's router output fails
    to parse. Not the primary classification mechanism."""
    from bioreason.pipeline.intent import PipelineIntentClassifier
    from bioreason.schemas.guided_pipeline import PipelineState

    intent = PipelineIntentClassifier().classify(user_message, PipelineState.IDLE, None)
    mapping = {
        "GENERAL_CHAT": "GENERAL_CHAT",
        "SCIENTIFIC_AUDIT": "SCIENTIFIC_AUDIT",
        "PIPELINE_BUILD": "PIPELINE_BUILD",
        "PIPELINE_DEBUG": "PIPELINE_DEBUG",
        "PIPELINE_EXPLAIN": "TEACHING",
        "CODE_ONLY": "CODE_EXPLANATION",
        "OTHER": "GENERAL_CHAT",
    }
    return mapping.get(intent.value, "GENERAL_CHAT")


def decide_mode(
    generate_fn,
    history: List[Dict[str, str]],
    user_message: str,
    pipeline_context_summary: Optional[str] = None,
    max_new_tokens: int = 60,
) -> RouterDecision:
    """generate_fn(messages) -> str: a callable that runs real model.generate()
    over the given chat messages and returns the decoded text. Supplied by the
    caller so this module stays model-loading-agnostic (used identically in
    eval harnesses and the chat backend)."""
    messages = build_router_messages(history, user_message, pipeline_context_summary)
    raw = generate_fn(messages, max_new_tokens)
    parsed = parse_router_output(raw)
    if parsed is not None:
        return RouterDecision(
            mode=parsed["mode"],
            confidence=float(parsed["confidence"]),
            explicit_user_request=bool(parsed.get("explicit_user_request", False)),
            raw_output=raw,
            parse_ok=True,
        )
    fallback_mode = keyword_fallback_mode(user_message)
    return RouterDecision(
        mode=fallback_mode,
        confidence=0.0,
        explicit_user_request=False,
        raw_output=raw,
        parse_ok=False,
        fallback_used=True,
    )

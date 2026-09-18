"""
Verified multi-turn conversational evaluation for BioReason Phase T1.5/T1.6.

Runs real model.generate() calls over BioReasonConversationDev-v0.1,
replaying each conversation turn-by-turn using the model's own prior
generations as context (not oracle answers), and computes format-pathology
metrics from the raw text. Never opens the sealed final benchmark.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .verified_sft_trainer import SYSTEM_PROMPT, collect_environment_manifest, get_git_info, sha256_file, write_json
from .verified_eval import GenerationConfigRecord, SEALED_PATH_MARKER, refuse_sealed_dataset

CORRECTED_SYSTEM_PROMPT = (
    "You are BioReason, a conversational scientific assistant specializing in "
    "biology, bioinformatics, experimental design, statistics, and "
    "computational biology. Respond naturally to ordinary questions. Use "
    "structured scientific audit formats only when they are appropriate or "
    "requested. Before building a pipeline, understand the user's experiment "
    "and ask for missing consequential information. Do not invent "
    "experimental details. Explain computational steps in terms accessible "
    "to biological scientists. Identify scientific flaws specifically, not "
    "merely by category."
)

RUBRIC_PHRASES = [
    "experimental unit", "primary issue", "severity", "scientific audit",
    "recommended remediation", "identified_issues", "flaw_detected",
    "recommended_analysis", "supported_claims", "unsupported_claims",
]
STOCK_PHRASES = [
    "rigorous methodology enforcing statistical invariants",
    "constrained to study parameters in",
    "validated invariant in",
]


@dataclass
class ConversationEvalConfig:
    run_id: str = "CONVERSATION-DEV-EVAL"
    base_model_path: str = "/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8"
    base_model_name: str = "Qwen/Qwen2.5-14B-Instruct"
    adapter_path: Optional[str] = None
    items_file: str = "benchmark/conversation_dev_v0.1/items.json"
    output_dir: str = "outputs/verified_training/conversation_dev/base_qwen"
    dtype: str = "bfloat16"
    system_prompt: str = SYSTEM_PROMPT
    seed: int = 42
    generation: GenerationConfigRecord = field(default_factory=lambda: GenerationConfigRecord(max_new_tokens=400))


def load_conversations(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    refuse_sealed_dataset(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data["items"] if isinstance(data, dict) else data
    by_conv: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        by_conv.setdefault(item["conversation_id"], []).append(item)
    for turns in by_conv.values():
        turns.sort(key=lambda t: t["turn_id"])
    return by_conv


def is_json_response(text: str) -> bool:
    stripped = text.strip()
    if not (stripped.startswith("{") or stripped.startswith("```json")):
        return False
    candidate = stripped
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        candidate = candidate[4:] if candidate.lower().startswith("json") else candidate
    try:
        json.loads(candidate)
        return True
    except Exception:
        return False


def has_rubric_language(text: str) -> bool:
    lower = text.lower()
    return any(p in lower for p in RUBRIC_PHRASES)


def has_stock_phrase(text: str) -> bool:
    lower = text.lower()
    return any(p in lower for p in STOCK_PHRASES)


AUDIT_HEADING_MARKERS = [
    "primary issue", "primary assessment", "why it matters", "secondary issue",
    "recommended correction", "confidence:", "experimental unit:",
]


def is_structured_audit_response(text: str) -> bool:
    """Detects readable structured-audit prose (headings/bold labels), not
    just raw JSON — the corrected system prompt teaches 'audit = structured
    reasoning', which may render as bolded headings rather than JSON."""
    lower = text.lower()
    heading_hits = sum(1 for marker in AUDIT_HEADING_MARKERS if marker in lower)
    bold_labels = len(re.findall(r"\*\*[^*]{3,40}:?\*\*", text))
    return heading_hits >= 2 or bold_labels >= 2


def classify_turn(text: str, expected_mode: str) -> Dict[str, Any]:
    structured_audit = is_structured_audit_response(text)
    is_audit_mode = expected_mode == "SCIENTIFIC_AUDIT"
    unwanted_json = is_json_response(text) and not is_audit_mode
    unwanted_rubric = has_rubric_language(text) and not is_audit_mode
    explicit_audit_compliant = (is_json_response(text) or structured_audit) if is_audit_mode else None
    return {
        "is_json": is_json_response(text),
        "is_structured_audit": structured_audit,
        "has_rubric_language": has_rubric_language(text),
        "has_stock_phrase": has_stock_phrase(text),
        "explicit_audit_compliant": explicit_audit_compliant,
        "unwanted_json": unwanted_json,
        "unwanted_rubric": unwanted_rubric,
        "word_count": len(text.split()),
    }


def run_conversation_eval(config: ConversationEvalConfig) -> Dict[str, Any]:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    env = collect_environment_manifest(output_dir)
    base = Path(config.base_model_path)
    if not (base / "config.json").exists():
        raise FileNotFoundError(f"Base model config not found: {base}")

    adapter_path = Path(config.adapter_path) if config.adapter_path else None
    adapter_sha256 = None
    if adapter_path is not None:
        adapter_file = adapter_path / "adapter_model.safetensors"
        if not adapter_file.exists():
            raise FileNotFoundError(f"Adapter weights not found: {adapter_file}")
        adapter_sha256 = sha256_file(adapter_file)

    items_path = Path(config.items_file)
    conversations = load_conversations(items_path)

    run_manifest = {
        "run_id": config.run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git": get_git_info(),
        "base_model_name": config.base_model_name,
        "base_model_snapshot": str(base),
        "adapter_path": str(adapter_path) if adapter_path else None,
        "adapter_model_sha256": adapter_sha256,
        "items_file": str(items_path),
        "items_file_sha256": sha256_file(items_path),
        "system_prompt": config.system_prompt,
        "generation_config": asdict(config.generation),
        "environment": env,
    }
    write_json(output_dir / "run_manifest.json", run_manifest)

    tokenizer = AutoTokenizer.from_pretrained(str(base), trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    dtype = torch.bfloat16 if config.dtype == "bfloat16" else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        str(base), torch_dtype=dtype, device_map="auto", trust_remote_code=True,
    )
    if adapter_path is not None:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, str(adapter_path))
        model = model.merge_and_unload()
    model.eval()

    records: List[Dict[str, Any]] = []
    predictions_path = output_dir / "conversation_predictions.jsonl"
    with predictions_path.open("w", encoding="utf-8") as f:
        for conv_id, turns in conversations.items():
            messages = [{"role": "system", "content": config.system_prompt}]
            for turn in turns:
                messages.append({"role": "user", "content": turn["user"]})
                prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
                start = time.time()
                with torch.no_grad():
                    generated = model.generate(
                        **inputs,
                        do_sample=config.generation.do_sample,
                        temperature=None if config.generation.temperature == 0 else config.generation.temperature,
                        top_p=config.generation.top_p,
                        max_new_tokens=config.generation.max_new_tokens,
                        repetition_penalty=config.generation.repetition_penalty,
                        pad_token_id=tokenizer.eos_token_id,
                    )
                latency = time.time() - start
                output_ids = generated[0][inputs["input_ids"].shape[-1]:]
                prediction = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
                messages.append({"role": "assistant", "content": prediction})

                classification = classify_turn(prediction, turn["expected_mode"])
                record = {
                    "conversation_id": conv_id,
                    "case_id": turn["case_id"],
                    "turn_id": turn["turn_id"],
                    "domain": turn["domain"],
                    "expected_mode": turn["expected_mode"],
                    "user": turn["user"],
                    "prediction": prediction,
                    "latency_seconds": latency,
                    "response_source": "MODEL_GENERATED",
                    "classification": classification,
                }
                records.append(record)
                f.write(json.dumps(record) + "\n")
                f.flush()

    metrics = aggregate_conversation_metrics(records)
    metrics_path = output_dir / "metrics.json"
    write_json(metrics_path, metrics)

    manifest = {
        "run_id": config.run_id,
        "status": "CONVERSATION_DEV_REAL_INFERENCE_COMPLETE",
        "response_source": "MODEL_GENERATED",
        "base_model_snapshot": str(base),
        "adapter_path": str(adapter_path) if adapter_path else None,
        "adapter_model_sha256": adapter_sha256,
        "n_turns": len(records),
        "n_conversations": len(conversations),
        "files": {
            "predictions": {"path": str(predictions_path), "sha256": sha256_file(predictions_path)},
            "metrics": {"path": str(metrics_path), "sha256": sha256_file(metrics_path)},
        },
        "metrics": metrics,
    }
    write_json(output_dir / "CONVERSATION_DEV_EVAL_MANIFEST.json", manifest)
    return manifest


def aggregate_conversation_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(records)
    if n == 0:
        return {"n": 0}

    def rate(pred) -> float:
        return sum(1 for r in records if pred(r)) / n

    by_mode: Dict[str, Dict[str, Any]] = {}
    for r in records:
        mode = r["expected_mode"]
        by_mode.setdefault(mode, {"n": 0, "unwanted_json": 0, "unwanted_rubric": 0, "stock_phrase": 0, "structured_audit": 0})
        by_mode[mode]["n"] += 1
        if r["classification"]["unwanted_json"]:
            by_mode[mode]["unwanted_json"] += 1
        if r["classification"]["unwanted_rubric"]:
            by_mode[mode]["unwanted_rubric"] += 1
        if r["classification"]["has_stock_phrase"]:
            by_mode[mode]["stock_phrase"] += 1
        if r["classification"]["is_structured_audit"]:
            by_mode[mode]["structured_audit"] += 1

    audit_records = [r for r in records if r["expected_mode"] == "SCIENTIFIC_AUDIT"]
    explicit_audit_compliance_rate = (
        sum(1 for r in audit_records if r["classification"]["explicit_audit_compliant"]) / len(audit_records)
        if audit_records else None
    )

    return {
        "n": n,
        "unwanted_json_rate": rate(lambda r: r["classification"]["unwanted_json"]),
        "unwanted_rubric_rate": rate(lambda r: r["classification"]["unwanted_rubric"]),
        "stock_phrase_rate": rate(lambda r: r["classification"]["has_stock_phrase"]),
        "natural_response_rate": rate(lambda r: not r["classification"]["is_json"]),
        "explicit_audit_compliance_rate": explicit_audit_compliance_rate,
        "explicit_audit_compliance_n": len(audit_records),
        "avg_word_count": sum(r["classification"]["word_count"] for r in records) / n,
        "by_expected_mode": by_mode,
        "metric_note": "Heuristic format-pathology proxy metrics computed from raw model generations; not simulated. "
                        "explicit_audit_compliance_rate credits both raw JSON and readable structured-audit prose "
                        "(bolded headings like Primary Issue / Why It Matters) as compliant, since the corrected "
                        "system prompt teaches structured reasoning, not JSON specifically.",
    }

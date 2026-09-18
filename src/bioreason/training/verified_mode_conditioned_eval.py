"""
Verified mode-conditioned evaluation for BioReason Phase T1.8.

Runs real model.generate() calls through the mode router + mode-overlay
orchestrator (bioreason.inference) over a conversational item set, and
computes both router-accuracy metrics (against the item's expected_mode
label) and the same format-pathology behavior metrics used for
unconditioned evaluation, so the two are directly comparable.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from bioreason.inference.orchestrator import run_orchestrated_turn
from .verified_sft_trainer import collect_environment_manifest, get_git_info, sha256_file, write_json
from .verified_eval import GenerationConfigRecord, aggregate_metrics, build_eval_prompt, load_items, score_prediction
from .verified_conversation_eval import classify_turn, load_conversations


@dataclass
class ModeConditionedEvalConfig:
    run_id: str = "MODE-CONDITIONED-EVAL"
    base_model_path: str = "/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8"
    base_model_name: str = "Qwen/Qwen2.5-14B-Instruct"
    adapter_path: Optional[str] = None
    items_file: str = "benchmark/conversation_dev_v0.1/items.json"
    output_dir: str = "outputs/verified_training/mode_conditioned/conversation_dev"
    dtype: str = "bfloat16"
    generation: GenerationConfigRecord = field(default_factory=lambda: GenerationConfigRecord(max_new_tokens=400))
    router_max_new_tokens: int = 80
    enable_two_pass_audit: bool = True


def run_mode_conditioned_eval(config: ModeConditionedEvalConfig) -> Dict[str, Any]:
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
        "base_model_snapshot": str(base),
        "adapter_path": str(adapter_path) if adapter_path else None,
        "adapter_model_sha256": adapter_sha256,
        "items_file": str(items_path),
        "items_file_sha256": sha256_file(items_path),
        "router_max_new_tokens": config.router_max_new_tokens,
        "enable_two_pass_audit": config.enable_two_pass_audit,
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

    def generate_fn(messages: List[Dict[str, str]], max_new_tokens: int) -> str:
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            generated = model.generate(
                **inputs,
                do_sample=config.generation.do_sample,
                temperature=None if config.generation.temperature == 0 else config.generation.temperature,
                top_p=config.generation.top_p,
                max_new_tokens=max_new_tokens,
                repetition_penalty=config.generation.repetition_penalty,
                pad_token_id=tokenizer.eos_token_id,
            )
        output_ids = generated[0][inputs["input_ids"].shape[-1]:]
        return tokenizer.decode(output_ids, skip_special_tokens=True).strip()

    records: List[Dict[str, Any]] = []
    predictions_path = output_dir / "mode_conditioned_predictions.jsonl"
    with predictions_path.open("w", encoding="utf-8") as f:
        for conv_id, turns in conversations.items():
            history: List[Dict[str, str]] = []
            for turn in turns:
                result = run_orchestrated_turn(
                    generate_fn=generate_fn,
                    history=history,
                    user_message=turn["user"],
                    main_max_new_tokens=config.generation.max_new_tokens,
                    router_max_new_tokens=config.router_max_new_tokens,
                    enable_two_pass_audit=config.enable_two_pass_audit,
                )
                history.append({"role": "user", "content": turn["user"]})
                history.append({"role": "assistant", "content": result.response})

                classification = classify_turn(result.response, turn["expected_mode"])
                record = {
                    "conversation_id": conv_id,
                    "case_id": turn["case_id"],
                    "turn_id": turn["turn_id"],
                    "domain": turn["domain"],
                    "expected_mode": turn["expected_mode"],
                    "user": turn["user"],
                    "router_mode": result.router.mode,
                    "router_confidence": result.router.confidence,
                    "router_explicit_user_request": result.router.explicit_user_request,
                    "router_parse_ok": result.router.parse_ok,
                    "router_fallback_used": result.router.fallback_used,
                    "router_raw_output": result.router.raw_output,
                    "system_prompt_used": result.system_prompt_used,
                    "prediction": result.response,
                    "audit_regeneration_used": result.audit_regeneration_used,
                    "latency_seconds": result.latency_seconds,
                    "response_source": "MODEL_GENERATED",
                    "classification": classification,
                }
                records.append(record)
                f.write(json.dumps(record) + "\n")
                f.flush()

    metrics = aggregate_mode_conditioned_metrics(records)
    metrics_path = output_dir / "metrics.json"
    write_json(metrics_path, metrics)

    manifest = {
        "run_id": config.run_id,
        "status": "MODE_CONDITIONED_EVAL_COMPLETE",
        "response_source": "MODEL_GENERATED",
        "adapter_model_sha256": adapter_sha256,
        "n_turns": len(records),
        "n_conversations": len(conversations),
        "files": {
            "predictions": {"path": str(predictions_path), "sha256": sha256_file(predictions_path)},
            "metrics": {"path": str(metrics_path), "sha256": sha256_file(metrics_path)},
        },
        "metrics": metrics,
    }
    write_json(output_dir / "MODE_CONDITIONED_EVAL_MANIFEST.json", manifest)
    return manifest


@dataclass
class ModeConditionedDevRegressionConfig:
    run_id: str = "MODE-CONDITIONED-DEV-REGRESSION"
    base_model_path: str = "/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8"
    adapter_path: Optional[str] = None
    dev_file: str = "benchmark/dev_v0.2/items.json"
    regression_file: str = "benchmark/regression/bioreason_regression_v0_1.json"
    output_dir: str = "outputs/verified_training/mode_conditioned/dev_regression"
    dtype: str = "bfloat16"
    max_items: Optional[int] = None
    generation: GenerationConfigRecord = field(default_factory=GenerationConfigRecord)
    router_max_new_tokens: int = 80
    enable_two_pass_audit: bool = True


def run_mode_conditioned_dev_regression(config: ModeConditionedDevRegressionConfig) -> Dict[str, Any]:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    base = Path(config.base_model_path)
    adapter_path = Path(config.adapter_path) if config.adapter_path else None

    tokenizer = AutoTokenizer.from_pretrained(str(base), trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    dtype = torch.bfloat16 if config.dtype == "bfloat16" else torch.float16
    model = AutoModelForCausalLM.from_pretrained(str(base), torch_dtype=dtype, device_map="auto", trust_remote_code=True)
    if adapter_path is not None:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, str(adapter_path))
        model = model.merge_and_unload()
    model.eval()

    def generate_fn(messages: List[Dict[str, str]], max_new_tokens: int) -> str:
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            generated = model.generate(
                **inputs, do_sample=config.generation.do_sample,
                temperature=None if config.generation.temperature == 0 else config.generation.temperature,
                top_p=config.generation.top_p, max_new_tokens=max_new_tokens,
                repetition_penalty=config.generation.repetition_penalty, pad_token_id=tokenizer.eos_token_id,
            )
        output_ids = generated[0][inputs["input_ids"].shape[-1]:]
        return tokenizer.decode(output_ids, skip_special_tokens=True).strip()

    def run_dataset(name: str, path: Path, out_path: Path) -> Dict[str, Any]:
        items = load_items(path)
        rows = items[: config.max_items] if config.max_items else items
        recs = []
        with out_path.open("w", encoding="utf-8") as f:
            for idx, item in enumerate(rows):
                prompt = build_eval_prompt(item)
                result = run_orchestrated_turn(
                    generate_fn=generate_fn, history=[], user_message=prompt,
                    main_max_new_tokens=config.generation.max_new_tokens,
                    router_max_new_tokens=config.router_max_new_tokens,
                    enable_two_pass_audit=config.enable_two_pass_audit,
                )
                rec = {
                    "dataset": name, "index": idx, "item_id": item.get("item_id"),
                    "router_mode": result.router.mode, "prediction": result.response,
                    "score": score_prediction(item, result.response), "response_source": "MODEL_GENERATED",
                }
                recs.append(rec)
                f.write(json.dumps(rec) + "\n")
                f.flush()
        m = aggregate_metrics(recs)
        m["prediction_file"] = str(out_path)
        return m

    dev_metrics = run_dataset("BioReasonDev-v0.2", Path(config.dev_file), output_dir / "dev_predictions.jsonl")
    reg_metrics = run_dataset("BioReasonRegression-v0.1", Path(config.regression_file), output_dir / "regression_predictions.jsonl")
    metrics = {"dev": dev_metrics, "regression": reg_metrics}
    write_json(output_dir / "metrics.json", metrics)
    return metrics


def aggregate_mode_conditioned_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(records)
    if n == 0:
        return {"n": 0}

    def rate(pred) -> float:
        return sum(1 for r in records if pred(r)) / n

    # Router accuracy / confusion matrix
    confusion: Dict[str, Dict[str, int]] = {}
    correct = 0
    for r in records:
        expected = r["expected_mode"]
        observed = r["router_mode"]
        confusion.setdefault(expected, {})
        confusion[expected][observed] = confusion[expected].get(observed, 0) + 1
        if expected == observed:
            correct += 1
    mode_accuracy = correct / n

    audit_records = [r for r in records if r["expected_mode"] == "SCIENTIFIC_AUDIT"]
    audit_recall = (
        sum(1 for r in audit_records if r["router_mode"] == "SCIENTIFIC_AUDIT") / len(audit_records)
        if audit_records else None
    )
    pipeline_expected = {"PIPELINE_INTAKE", "PIPELINE_BUILD", "PIPELINE_FOLLOWUP", "PIPELINE_DEBUG"}
    pipeline_records = [r for r in records if r["expected_mode"] in pipeline_expected]
    pipeline_recall = (
        sum(1 for r in pipeline_records if r["router_mode"] in pipeline_expected) / len(pipeline_records)
        if pipeline_records else None
    )
    debug_records = [r for r in records if r["expected_mode"] in ("PIPELINE_DEBUG", "DEBUGGING")]
    debug_recall = (
        sum(1 for r in debug_records if r["router_mode"] in ("PIPELINE_DEBUG", "DEBUGGING")) / len(debug_records)
        if debug_records else None
    )

    explicit_audit_compliance_rate = (
        sum(1 for r in audit_records if r["classification"]["explicit_audit_compliant"]) / len(audit_records)
        if audit_records else None
    )

    return {
        "n": n,
        "router": {
            "mode_accuracy": mode_accuracy,
            "explicit_audit_recall": audit_recall,
            "pipeline_intent_recall": pipeline_recall,
            "debugging_recall": debug_recall,
            "router_parse_failure_rate": rate(lambda r: not r["router_parse_ok"]),
            "confusion_matrix": confusion,
        },
        "behavior": {
            "unwanted_json_rate": rate(lambda r: r["classification"]["unwanted_json"]),
            "unwanted_rubric_rate": rate(lambda r: r["classification"]["unwanted_rubric"]),
            "stock_phrase_rate": rate(lambda r: r["classification"]["has_stock_phrase"]),
            "natural_response_rate": rate(lambda r: not r["classification"]["is_json"]),
            "explicit_audit_compliance_rate": explicit_audit_compliance_rate,
            "explicit_audit_compliance_n": len(audit_records),
            "avg_word_count": sum(r["classification"]["word_count"] for r in records) / n,
            "audit_regeneration_used_rate": rate(lambda r: r["audit_regeneration_used"]),
        },
        "metric_note": "Real model_generated router + main-pass metrics; router accuracy computed against item expected_mode labels.",
    }

"""
Verified generation-based evaluation for BioReason Phase T1.

This module performs actual model.generate calls and computes lightweight,
reproducible metrics from the raw predictions. It never opens the sealed final
benchmark.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .verified_sft_trainer import SYSTEM_PROMPT, collect_environment_manifest, get_git_info, sha256_file, write_json


SEALED_PATH_MARKER = "benchmark/final_v0.2"


@dataclass
class GenerationConfigRecord:
    temperature: float = 0.0
    do_sample: bool = False
    max_new_tokens: int = 512
    top_p: Optional[float] = None
    repetition_penalty: float = 1.0


@dataclass
class VerifiedEvalConfig:
    run_id: str = "BASELINE-QWEN-VERIFIED-001"
    base_model_path: str = "/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8"
    base_model_name: str = "Qwen/Qwen2.5-14B-Instruct"
    adapter_path: Optional[str] = None
    dev_file: str = "benchmark/dev_v0.2/items.json"
    regression_file: str = "benchmark/regression/bioreason_regression_v0_1.json"
    output_dir: str = "outputs/verified_training/baseline_qwen"
    dtype: str = "bfloat16"
    max_items: Optional[int] = None
    seed: int = 42
    generation: GenerationConfigRecord = field(default_factory=GenerationConfigRecord)


def refuse_sealed_dataset(path: Path) -> None:
    normalized = str(path).replace("\\", "/")
    if SEALED_PATH_MARKER in normalized or "BioReasonBench-v0.2-Final" in normalized:
        raise RuntimeError(f"Refusing to open sealed final benchmark: {path}")


def load_items(path: Path) -> List[Dict[str, Any]]:
    refuse_sealed_dataset(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return data["items"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unsupported evaluation file shape: {path}")


def build_eval_prompt(item: Dict[str, Any]) -> str:
    return (
        "Evaluate this biological research scenario. Identify whether the proposed "
        "analysis is valid, explain the primary issue if any, and propose a defensible correction.\n\n"
        f"Scenario:\n{item.get('scenario', '')}\n\n"
        f"Question:\n{item.get('question', '')}"
    )


def build_generation_messages(item: Dict[str, Any]) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_eval_prompt(item)},
    ]


def keyword_hit(text: str, keywords: Iterable[str]) -> bool:
    lower = text.lower()
    return any(k.lower() in lower for k in keywords if k)


def score_prediction(item: Dict[str, Any], prediction: str) -> Dict[str, Any]:
    rubric = item.get("scoring_rubric", {})
    flaw_type = item.get("flaw_type")
    flawed = bool(item.get("flawed_analysis_present", False))
    detection_keywords = [flaw_type] if flaw_type else []
    detection_keywords += rubric.get("flaw_detection", {}).get("key_points", [])
    correction_keywords = rubric.get("correction_quality", {}).get("key_points", [])
    negative_keywords = []
    for section in rubric.values():
        if isinstance(section, dict):
            negative_keywords += section.get("negative_points", [])

    flaw_detected = keyword_hit(prediction, detection_keywords)
    correction_hit = keyword_hit(prediction, correction_keywords)
    negative_hit = keyword_hit(prediction, negative_keywords)
    valid_recognized = (not flawed) and keyword_hit(
        prediction,
        ["valid", "reasonable", "defensible", "appropriate", "no major flaw"],
    )
    if flawed:
        correctness = flaw_detected and not negative_hit
    else:
        correctness = valid_recognized and not negative_hit
    return {
        "expected_flawed": flawed,
        "flaw_type": flaw_type,
        "flaw_detected_keyword": flaw_detected,
        "correction_keyword_hit": correction_hit,
        "negative_keyword_hit": negative_hit,
        "valid_recognized_keyword": valid_recognized,
        "correctness_proxy": correctness,
    }


def aggregate_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        return {"n": 0}
    n = len(records)
    scored = [r["score"] for r in records]
    flawed = [s for s in scored if s["expected_flawed"]]
    valid = [s for s in scored if not s["expected_flawed"]]

    def rate(rows: List[Dict[str, Any]], key: str) -> Optional[float]:
        if not rows:
            return None
        return sum(1 for r in rows if r[key]) / len(rows)

    return {
        "n": n,
        "correctness_proxy_rate": rate(scored, "correctness_proxy"),
        "flawed_n": len(flawed),
        "valid_n": len(valid),
        "flaw_detection_keyword_rate": rate(flawed, "flaw_detected_keyword"),
        "valid_recognition_keyword_rate": rate(valid, "valid_recognized_keyword"),
        "correction_keyword_rate": rate(scored, "correction_keyword_hit"),
        "negative_keyword_rate": rate(scored, "negative_keyword_hit"),
        "metric_note": "Keyword proxy metrics computed from raw model generations; not simulated performance.",
    }


def run_generation_dataset(
    *,
    model: Any,
    tokenizer: Any,
    dataset_name: str,
    items: List[Dict[str, Any]],
    output_path: Path,
    generation: GenerationConfigRecord,
    max_items: Optional[int],
) -> Dict[str, Any]:
    import torch

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = items[:max_items] if max_items else items
    records: List[Dict[str, Any]] = []
    start_all = time.time()
    with output_path.open("w", encoding="utf-8") as f:
        for index, item in enumerate(rows):
            messages = build_generation_messages(item)
            if hasattr(tokenizer, "apply_chat_template"):
                prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            else:
                prompt = f"{SYSTEM_PROMPT}\n\nUSER: {messages[-1]['content']}\nASSISTANT:"
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            input_tokens = int(inputs["input_ids"].shape[-1])
            start = time.time()
            with torch.no_grad():
                generated = model.generate(
                    **inputs,
                    do_sample=generation.do_sample,
                    temperature=None if generation.temperature == 0 else generation.temperature,
                    top_p=generation.top_p,
                    max_new_tokens=generation.max_new_tokens,
                    repetition_penalty=generation.repetition_penalty,
                    pad_token_id=tokenizer.eos_token_id,
                )
            latency = time.time() - start
            output_ids = generated[0][inputs["input_ids"].shape[-1] :]
            prediction = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
            output_tokens = int(output_ids.shape[-1])
            record = {
                "dataset": dataset_name,
                "index": index,
                "item_id": item.get("item_id"),
                "prompt": prompt,
                "prediction": prediction,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_seconds": latency,
                "score": score_prediction(item, prediction),
                "response_source": "MODEL_GENERATED",
            }
            records.append(record)
            f.write(json.dumps(record) + "\n")
            f.flush()
    metrics = aggregate_metrics(records)
    metrics["latency_seconds_total"] = time.time() - start_all
    metrics["prediction_file"] = str(output_path)
    metrics["prediction_file_sha256"] = sha256_file(output_path)
    return metrics


def run_verified_baseline(config: VerifiedEvalConfig) -> Dict[str, Any]:
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

    generation_config_path = output_dir / "generation_config.json"
    write_json(generation_config_path, asdict(config.generation))
    run_manifest = {
        "run_id": config.run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git": get_git_info(),
        "base_model_name": config.base_model_name,
        "base_model_snapshot": str(base),
        "base_model_snapshot_id": base.name,
        "adapter_path": str(adapter_path) if adapter_path else None,
        "adapter_model_sha256": adapter_sha256,
        "dev_file": config.dev_file,
        "dev_file_sha256": sha256_file(Path(config.dev_file)),
        "regression_file": config.regression_file,
        "regression_file_sha256": sha256_file(Path(config.regression_file)),
        "generation_config": asdict(config.generation),
        "environment": env,
    }
    write_json(output_dir / "run_manifest.json", run_manifest)

    tokenizer = AutoTokenizer.from_pretrained(str(base), trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    dtype = torch.bfloat16 if config.dtype == "bfloat16" else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        str(base),
        torch_dtype=dtype,
        device_map="auto",
        trust_remote_code=True,
    )
    if adapter_path is not None:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, str(adapter_path))
        model = model.merge_and_unload()
    model.eval()

    dev_metrics = run_generation_dataset(
        model=model,
        tokenizer=tokenizer,
        dataset_name="BioReasonDev-v0.2",
        items=load_items(Path(config.dev_file)),
        output_path=output_dir / "dev_predictions.jsonl",
        generation=config.generation,
        max_items=config.max_items,
    )
    regression_metrics = run_generation_dataset(
        model=model,
        tokenizer=tokenizer,
        dataset_name="BioReasonRegression-v0.1",
        items=load_items(Path(config.regression_file)),
        output_path=output_dir / "regression_predictions.jsonl",
        generation=config.generation,
        max_items=config.max_items,
    )
    metrics = {"dev": dev_metrics, "regression": regression_metrics}
    metrics_path = output_dir / "metrics.json"
    write_json(metrics_path, metrics)
    manifest = {
        "run_id": config.run_id,
        "status": "VERIFIED_REAL_INFERENCE_COMPLETE",
        "response_source": "MODEL_GENERATED",
        "base_model_snapshot": str(base),
        "adapter_path": str(adapter_path) if adapter_path else None,
        "adapter_model_sha256": adapter_sha256,
        "files": {
            "dev_predictions": {
                "path": str(output_dir / "dev_predictions.jsonl"),
                "sha256": sha256_file(output_dir / "dev_predictions.jsonl"),
            },
            "regression_predictions": {
                "path": str(output_dir / "regression_predictions.jsonl"),
                "sha256": sha256_file(output_dir / "regression_predictions.jsonl"),
            },
            "metrics": {"path": str(metrics_path), "sha256": sha256_file(metrics_path)},
            "generation_config": {
                "path": str(generation_config_path),
                "sha256": sha256_file(generation_config_path),
            },
        },
        "metrics": metrics,
    }
    manifest_name = "BASELINE_QWEN_VERIFIED_MANIFEST.json" if adapter_path is None else "SFT_VERIFIED_EVAL_MANIFEST.json"
    write_json(output_dir / manifest_name, manifest)
    return manifest

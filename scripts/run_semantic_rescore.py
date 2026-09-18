#!/usr/bin/env python3
"""
Re-scores every existing Dev/Regression prediction file with a real
LLM-judge semantic scorer, instead of the literal keyword matcher. Does
NOT regenerate any model predictions — pure re-analysis of what's already
on disk. Loads base Qwen (no adapter) as the judge model.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioreason.training.semantic_judge import (
    build_extract_prompt,
    build_compare_prompt,
    parse_extract_output,
    parse_compare_output,
    EXTRACT_INSTRUCTION,
    COMPARE_INSTRUCTION,
)
from bioreason.training.verified_sft_trainer import sha256_file, write_json


PREDICTION_SETS = [
    ("Base Qwen", "outputs/verified_training/baseline_qwen/dev_predictions.jsonl", "benchmark/dev_v0.2/items.json", "dev"),
    ("Base Qwen", "outputs/verified_training/baseline_qwen/regression_predictions.jsonl", "benchmark/regression/bioreason_regression_v0_1.json", "regression"),
    ("SFT-001", "outputs/verified_training/BR-VERIFIED-SFT-001/eval/dev_predictions.jsonl", "benchmark/dev_v0.2/items.json", "dev"),
    ("SFT-001", "outputs/verified_training/BR-VERIFIED-SFT-001/eval/regression_predictions.jsonl", "benchmark/regression/bioreason_regression_v0_1.json", "regression"),
    ("SFT-002", "outputs/verified_training/BR-VERIFIED-SFT-002/eval/dev_predictions.jsonl", "benchmark/dev_v0.2/items.json", "dev"),
    ("SFT-002", "outputs/verified_training/BR-VERIFIED-SFT-002/eval/regression_predictions.jsonl", "benchmark/regression/bioreason_regression_v0_1.json", "regression"),
    ("SFT-003", "outputs/verified_training/BR-VERIFIED-SFT-003/eval/dev_predictions.jsonl", "benchmark/dev_v0.2/items.json", "dev"),
    ("SFT-003", "outputs/verified_training/BR-VERIFIED-SFT-003/eval/regression_predictions.jsonl", "benchmark/regression/bioreason_regression_v0_1.json", "regression"),
    ("SFT-002 mode-conditioned", "outputs/verified_training/mode_conditioned/dev_regression/dev_predictions.jsonl", "benchmark/dev_v0.2/items.json", "dev"),
    ("SFT-002 mode-conditioned", "outputs/verified_training/mode_conditioned/dev_regression/regression_predictions.jsonl", "benchmark/regression/bioreason_regression_v0_1.json", "regression"),
    ("SFT-002 mode-conditioned v2overlay", "outputs/verified_training/mode_conditioned_v2overlay/dev_regression/dev_predictions.jsonl", "benchmark/dev_v0.2/items.json", "dev"),
    ("SFT-002 mode-conditioned v2overlay", "outputs/verified_training/mode_conditioned_v2overlay/dev_regression/regression_predictions.jsonl", "benchmark/regression/bioreason_regression_v0_1.json", "regression"),
    ("DPO-001", "outputs/verified_training/BR-VERIFIED-DPO-001/eval/dev_predictions.jsonl", "benchmark/dev_v0.2/items.json", "dev"),
    ("DPO-001", "outputs/verified_training/BR-VERIFIED-DPO-001/eval/regression_predictions.jsonl", "benchmark/regression/bioreason_regression_v0_1.json", "regression"),
    ("DPO-002", "outputs/verified_training/BR-VERIFIED-DPO-002/eval/dev_predictions.jsonl", "benchmark/dev_v0.2/items.json", "dev"),
    ("DPO-002", "outputs/verified_training/BR-VERIFIED-DPO-002/eval/regression_predictions.jsonl", "benchmark/regression/bioreason_regression_v0_1.json", "regression"),
]


def load_items_by_index(path: str):
    data = json.loads(Path(path).read_text())
    return data["items"] if isinstance(data, dict) and "items" in data else data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge-model-path", required=True)
    parser.add_argument("--output-dir", default="outputs/verified_training/semantic_rescore")
    parser.add_argument("--max-new-tokens", type=int, default=120)
    parser.add_argument("--only", help="substring filter on model_name; only run matching prediction sets")
    args = parser.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(args.judge_model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.judge_model_path, torch_dtype=torch.bfloat16, device_map="auto", trust_remote_code=True,
    )
    model.eval()

    def call_model(system: str, user: str, max_new_tokens: int) -> str:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            generated = model.generate(
                **inputs, do_sample=False, max_new_tokens=max_new_tokens,
                pad_token_id=tokenizer.eos_token_id,
            )
        output_ids = generated[0][inputs["input_ids"].shape[-1]:]
        return tokenizer.decode(output_ids, skip_special_tokens=True).strip()

    def judge(scenario, question, flawed, flaw_type, rationale, key_points, prediction) -> dict:
        # Step 1: extract what the response itself claims, blind to the reference.
        extract_prompt = build_extract_prompt(scenario, question, prediction)
        extract_raw = call_model(EXTRACT_INSTRUCTION, extract_prompt, args.max_new_tokens)
        extracted = parse_extract_output(extract_raw)
        if extracted is None:
            return {"correct": None, "confidence": 0.0, "justification": "EXTRACT_PARSE_FAILURE", "raw": extract_raw}

        # Step 2: compare the extraction (not the raw response) against the reference.
        compare_prompt = build_compare_prompt(
            flawed, flaw_type, rationale, key_points,
            extracted["claimed_valid"], extracted["claimed_mechanism_summary"], extracted["is_generic_label_only"],
        )
        compare_raw = call_model(COMPARE_INSTRUCTION, compare_prompt, args.max_new_tokens)
        compared = parse_compare_output(compare_raw)
        if compared is None:
            return {"correct": None, "confidence": 0.0, "justification": "COMPARE_PARSE_FAILURE", "raw": compare_raw, "extracted": extracted}
        compared["raw"] = compare_raw
        compared["extracted"] = extracted
        return compared

    summary = {}
    for model_name, pred_path, items_path, dataset_name in PREDICTION_SETS:
        if args.only and args.only not in model_name:
            continue
        pred_file = Path(pred_path)
        if not pred_file.exists():
            continue
        preds = [json.loads(l) for l in pred_file.open()]
        items = load_items_by_index(items_path)

        out_name = f"{model_name.replace(' ', '_')}_{dataset_name}_semantic.jsonl"
        out_path = output_dir / out_name
        n_correct = 0
        n_judged = 0
        n_parse_fail = 0
        recs = []
        t0 = time.time()
        with out_path.open("w", encoding="utf-8") as f:
            for pred, item in zip(preds, items):
                flawed = bool(item.get("flawed_analysis_present", False))
                result = judge(
                    scenario=item.get("scenario", ""),
                    question=item.get("question", ""),
                    flawed=flawed,
                    flaw_type=item.get("flaw_type"),
                    rationale=item.get("ground_truth_rationale"),
                    key_points=item.get("scoring_rubric", {}).get("flaw_detection", {}).get("key_points"),
                    prediction=pred.get("prediction", ""),
                )
                rec = {
                    "item_id": item.get("item_id"),
                    "flawed": flawed,
                    "flaw_type": item.get("flaw_type"),
                    "keyword_scored_correct": pred.get("score", {}).get("correctness_proxy"),
                    "semantic_judge_correct": result["correct"],
                    "semantic_judge_confidence": result.get("confidence"),
                    "semantic_judge_justification": result.get("justification"),
                    "extracted_claim": result.get("extracted"),
                }
                recs.append(rec)
                f.write(json.dumps(rec) + "\n")
                f.flush()
                if result["correct"] is None:
                    n_parse_fail += 1
                else:
                    n_judged += 1
                    if result["correct"]:
                        n_correct += 1

        semantic_rate = n_correct / n_judged if n_judged else None
        keyword_rate = sum(1 for r in recs if r["keyword_scored_correct"]) / len(recs) if recs else None
        key = f"{model_name} / {dataset_name}"
        summary[key] = {
            "n": len(recs),
            "n_judged": n_judged,
            "n_parse_fail": n_parse_fail,
            "semantic_correctness_rate": semantic_rate,
            "original_keyword_correctness_rate": keyword_rate,
            "elapsed_seconds": time.time() - t0,
            "predictions_file_sha256": sha256_file(pred_file),
            "output_file": str(out_path),
        }
        print(json.dumps({key: summary[key]}, indent=2))

    write_json(output_dir / "SEMANTIC_RESCORE_SUMMARY.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

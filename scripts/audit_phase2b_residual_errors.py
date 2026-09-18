"""
Audit script for Phase 2B residual scientific reasoning failures from Epoch 2.0 SFT checkpoint.
Analyzes each of the 289 development benchmark items, groups failures into canonical taxonomy,
and outputs detailed statistics and examples.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

from bioreason.schemas.benchmark import BenchmarkItem, EvaluationScore, DifficultyLevel, BenchmarkCategory
from bioreason.models.base import ModelPrediction
from bioreason.evaluation.rubric import ScientificRubricScorer
from bioreason.datasets.loader import load_benchmark_from_dir


def audit_residual_errors():
    dev_dir = Path("benchmark/frozen/bioreasonbench_v0.1/dev")
    benchmark_items = load_benchmark_from_dir(dev_dir)
    scorer = ScientificRubricScorer()

    ckpt_pred_file = Path("outputs/BR-SFT-001-A/checkpoint-epoch-2.0/benchmark_predictions.jsonl")
    predictions = []
    with open(ckpt_pred_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                predictions.append(ModelPrediction.model_validate_json(line))

    pred_map = {p.item_id: p for p in predictions}

    taxonomy_buckets = defaultdict(list)
    item_results = []

    for item in benchmark_items:
        pred = pred_map.get(item.item_id)
        if not pred:
            continue

        score = scorer.evaluate_prediction(item, pred)
        item_results.append((item, pred, score))

        # 1. False Alarms on Valid Hard Negatives
        if not item.flawed_analysis_present and score.false_alarm:
            taxonomy_buckets["SCIENTIFIC_FALSE_ALARM"].append({
                "item_id": item.item_id,
                "category": item.category.value,
                "difficulty": item.difficulty.value,
                "scenario": item.scenario,
                "model_assessment": pred.primary_assessment,
                "model_issues": pred.identified_issues,
                "ground_truth": item.ground_truth_rationale,
                "severity": "SERIOUS",
            })

        # 2. Critical Failures on Flawed Cases
        if item.flawed_analysis_present and score.critical_failure:
            ft = (item.flaw_type or "").lower()
            if "leak" in ft:
                mode = "MISSED_LEAKAGE"
            elif "pseudo" in ft:
                mode = "MISSED_PSEUDOREPLICATION"
            elif "batch" in ft or "confound" in ft:
                mode = "MISSED_CONFOUNDING"
            elif "transform" in ft or "count" in ft:
                mode = "INVALID_TRANSFORMATION"
            else:
                mode = "MISSED_CRITICAL_ERROR"

            taxonomy_buckets[mode].append({
                "item_id": item.item_id,
                "category": item.category.value,
                "difficulty": item.difficulty.value,
                "scenario": item.scenario,
                "model_assessment": pred.primary_assessment,
                "ground_truth": item.ground_truth_rationale,
                "severity": "CRITICAL",
            })

        # 3. Weak / Non-Actionable Corrections
        if item.flawed_analysis_present and score.flaw_detected_binary and score.correction_score < 0.40:
            taxonomy_buckets["WEAK_CORRECTION"].append({
                "item_id": item.item_id,
                "category": item.category.value,
                "difficulty": item.difficulty.value,
                "scenario": item.scenario,
                "proposed_correction": pred.proposed_correction,
                "ground_truth": item.ground_truth_rationale,
                "severity": "WARNING",
            })

        # 4. Primary Issue Prioritization Failures
        if item.flawed_analysis_present and not score.primary_issue_prioritized:
            taxonomy_buckets["WRONG_PRIMARY_ISSUE"].append({
                "item_id": item.item_id,
                "category": item.category.value,
                "difficulty": item.difficulty.value,
                "scenario": item.scenario,
                "expected_primary": item.expected_decision.primary_issue if item.expected_decision else "unknown",
                "model_first_issue": pred.identified_issues[0] if pred.identified_issues else "none",
                "severity": "SERIOUS",
            })

        # 5. Insufficient Information Handling
        if ("insufficient" in (item.flaw_type or "").lower() or "insufficient" in item.ground_truth_rationale.lower()) and not score.flaw_detected_binary:
            taxonomy_buckets["FAILED_UNCERTAINTY"].append({
                "item_id": item.item_id,
                "category": item.category.value,
                "difficulty": item.difficulty.value,
                "scenario": item.scenario,
                "model_assessment": pred.primary_assessment,
                "ground_truth": item.ground_truth_rationale,
                "severity": "WARNING",
            })

        # 6. Causality / Biomarker Overclaims
        if ("causal" in (item.flaw_type or "").lower() or "shap" in (item.flaw_type or "").lower()) and not score.flaw_detected_binary:
            taxonomy_buckets["OVERCLAIMED_CAUSALITY"].append({
                "item_id": item.item_id,
                "category": item.category.value,
                "difficulty": item.difficulty.value,
                "scenario": item.scenario,
                "model_assessment": pred.primary_assessment,
                "ground_truth": item.ground_truth_rationale,
                "severity": "SERIOUS",
            })

    print("==================================================")
    print("PHASE 2B RESIDUAL ERROR AUDIT SUMMARY (Epoch 2.0)")
    print("==================================================")
    for tax, items in sorted(taxonomy_buckets.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"Taxonomy: {tax:<30} Count: {len(items):<4} Rate: {len(items)/289*100:5.2f}%")

    # Write JSON summary
    with open("eval_results/phase2b_residual_error_summary.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_items_audited": len(item_results),
            "taxonomy_counts": {k: len(v) for k, v in taxonomy_buckets.items()},
            "taxonomy_details": taxonomy_buckets,
        }, f, indent=2)

    return taxonomy_buckets


if __name__ == "__main__":
    audit_residual_errors()

"""
Multi-dimensional evaluation metrics for scientific reasoning benchmarks with difficulty, category, and critical failure breakdowns.
"""

from typing import List, Dict, Any
from bioreason.schemas.benchmark import EvaluationScore, DifficultyLevel


def compute_aggregate_benchmark_metrics(scores: List[EvaluationScore]) -> Dict[str, Any]:
    if not scores:
        return {
            "total_items": 0,
            "mean_composite_score": 0.0,
            "mean_flaw_detection_score": 0.0,
            "mean_explanation_score": 0.0,
            "mean_correction_score": 0.0,
            "mean_calibration_score": 0.0,
            "mean_interpretation_score": 0.0,
            "flaw_detection_accuracy": 0.0,
            "critical_failure_rate": 0.0,
            "by_difficulty": {},
            "failure_taxonomy_counts": {},
        }

    n = len(scores)
    mean_composite = sum(s.composite_score for s in scores) / n
    mean_flaw = sum(s.flaw_detection_score for s in scores) / n
    mean_exp = sum(s.explanation_score for s in scores) / n
    mean_corr = sum(s.correction_score for s in scores) / n
    mean_calib = sum(s.calibration_score for s in scores) / n
    mean_interp = sum(s.interpretation_score for s in scores) / n
    flaw_acc = sum(1 for s in scores if s.flaw_detected_binary) / n
    crit_failures = sum(1 for s in scores if s.critical_failure)
    crit_fail_rate = crit_failures / n

    # Breakdown by difficulty
    by_diff: Dict[str, Dict[str, Any]] = {}
    for diff in DifficultyLevel:
        diff_scores = [s for s in scores if s.difficulty == diff]
        if diff_scores:
            dn = len(diff_scores)
            by_diff[diff.value] = {
                "count": dn,
                "mean_composite": round(sum(s.composite_score for s in diff_scores) / dn, 4),
                "flaw_accuracy": round(sum(1 for s in diff_scores if s.flaw_detected_binary) / dn, 4),
                "critical_failure_rate": round(sum(1 for s in diff_scores if s.critical_failure) / dn, 4),
            }

    # Failure taxonomy aggregation
    taxonomy_counts: Dict[str, int] = {}
    for s in scores:
        for mode in s.identified_failure_modes:
            taxonomy_counts[mode] = taxonomy_counts.get(mode, 0) + 1

    return {
        "total_items": n,
        "mean_composite_score": round(mean_composite, 4),
        "mean_flaw_detection_score": round(mean_flaw, 4),
        "mean_explanation_score": round(mean_exp, 4),
        "mean_correction_score": round(mean_corr, 4),
        "mean_calibration_score": round(mean_calib, 4),
        "mean_interpretation_score": round(mean_interp, 4),
        "flaw_detection_accuracy": round(flaw_acc, 4),
        "critical_failure_rate": round(crit_fail_rate, 4),
        "total_critical_failures": crit_failures,
        "by_difficulty": by_diff,
        "failure_taxonomy_counts": taxonomy_counts,
    }

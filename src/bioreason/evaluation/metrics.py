"""
Multi-dimensional evaluation metrics for scientific reasoning benchmarks.
"""

from typing import List, Dict, Any
from bioreason.schemas.benchmark import EvaluationScore


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
        }

    n = len(scores)
    mean_composite = sum(s.composite_score for s in scores) / n
    mean_flaw = sum(s.flaw_detection_score for s in scores) / n
    mean_exp = sum(s.explanation_score for s in scores) / n
    mean_corr = sum(s.correction_score for s in scores) / n
    mean_calib = sum(s.calibration_score for s in scores) / n
    mean_interp = sum(s.interpretation_score for s in scores) / n
    flaw_acc = sum(1 for s in scores if s.flaw_detected_binary) / n

    return {
        "total_items": n,
        "mean_composite_score": round(mean_composite, 4),
        "mean_flaw_detection_score": round(mean_flaw, 4),
        "mean_explanation_score": round(mean_exp, 4),
        "mean_correction_score": round(mean_corr, 4),
        "mean_calibration_score": round(mean_calib, 4),
        "mean_interpretation_score": round(mean_interp, 4),
        "flaw_detection_accuracy": round(flaw_acc, 4),
    }

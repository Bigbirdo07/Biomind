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
            "scientific_false_alarm_rate": 0.0,
            "valid_hard_negative_accuracy": 0.0,
            "no_error_accuracy": 0.0,
            "insufficient_information_accuracy": 0.0,
            "high_confidence_critical_error_rate": 0.0,
            "bioreason_balance_score": 0.0,
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
    
    # Hard negative and false alarm metrics
    hard_negatives = [s for s in scores if s.is_hard_negative]
    n_hn = len(hard_negatives)
    if n_hn > 0:
        hn_correct = sum(1 for s in hard_negatives if s.no_error_correct)
        hn_acc = hn_correct / n_hn
        false_alarms = sum(1 for s in hard_negatives if s.false_alarm)
        false_alarm_rate = false_alarms / n_hn
    else:
        hn_acc = 1.0
        false_alarms = sum(1 for s in scores if s.false_alarm)
        false_alarm_rate = false_alarms / n if n > 0 else 0.0

    no_error_acc = hn_acc

    # Insufficient information metrics
    insufficient_items = [s for s in scores if s.is_insufficient_info]
    n_insuf = len(insufficient_items)
    insuf_acc = (sum(1 for s in insufficient_items if s.flaw_detected_binary) / n_insuf) if n_insuf > 0 else 1.0

    # High-confidence critical failures
    high_conf_crit = sum(1 for s in scores if s.high_confidence_critical_error)
    high_conf_crit_rate = high_conf_crit / n

    mean_actionability = sum(s.correction_actionability_score or 0.0 for s in scores) / n if n > 0 else 0.0
    issue_prio_rate = sum(1 for s in scores if s.primary_issue_prioritized) / n if n > 0 else 0.0

    # BIOREASON_BALANCE_SCORE Calculation
    # Positive signals: Flaw Detection (0.25), Valid Hard Negatives (0.25), Correction (0.25), Calibration (0.25)
    # Penalties: Critical Failures (0.35), False Alarms (0.35), High Confidence Critical Errors (0.30)
    positive_signal = (
        0.25 * flaw_acc
        + 0.25 * hn_acc
        + 0.25 * mean_corr
        + 0.25 * mean_calib
    )
    penalties = (
        0.35 * crit_fail_rate
        + 0.35 * false_alarm_rate
        + 0.30 * high_conf_crit_rate
    )
    bioreason_balance_score = round(max(-1.0, min(1.0, positive_signal - penalties)), 4)

    # Breakdown by difficulty
    by_diff: Dict[str, Dict[str, Any]] = {}
    for diff in DifficultyLevel:
        diff_scores = [s for s in scores if s.difficulty == diff]
        if diff_scores:
            dn = len(diff_scores)
            d_hn = [s for s in diff_scores if s.is_hard_negative]
            d_fa = sum(1 for s in d_hn if s.false_alarm) if d_hn else sum(1 for s in diff_scores if s.false_alarm)
            d_fa_rate = (d_fa / len(d_hn)) if d_hn else (d_fa / dn)
            by_diff[diff.value] = {
                "count": dn,
                "mean_composite": round(sum(s.composite_score for s in diff_scores) / dn, 4),
                "flaw_accuracy": round(sum(1 for s in diff_scores if s.flaw_detected_binary) / dn, 4),
                "critical_failure_rate": round(sum(1 for s in diff_scores if s.critical_failure) / dn, 4),
                "scientific_false_alarm_rate": round(d_fa_rate, 4),
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
        "mean_correction_actionability": round(mean_actionability, 4),
        "mean_calibration_score": round(mean_calib, 4),
        "mean_interpretation_score": round(mean_interp, 4),
        "flaw_detection_accuracy": round(flaw_acc, 4),
        "critical_failure_rate": round(crit_fail_rate, 4),
        "scientific_false_alarm_rate": round(false_alarm_rate, 4),
        "valid_hard_negative_accuracy": round(hn_acc, 4),
        "no_error_accuracy": round(no_error_acc, 4),
        "insufficient_information_accuracy": round(insuf_acc, 4),
        "high_confidence_critical_error_rate": round(high_conf_crit_rate, 4),
        "bioreason_balance_score": bioreason_balance_score,
        "primary_issue_prioritization_rate": round(issue_prio_rate, 4),
        "total_critical_failures": crit_failures,
        "by_difficulty": by_diff,
        "failure_taxonomy_counts": taxonomy_counts,
    }



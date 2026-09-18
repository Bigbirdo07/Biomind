"""
Baseline Audit & Bootstrap Confidence Interval Engine.
Performs stratified output inspection, bootstrap resampling (95% CIs),
and audits the 14B underperformance and 32B zero-critical-failure results.
"""

import json
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple
from bioreason.schemas.benchmark import DifficultyLevel
from bioreason.datasets.loader import load_benchmark_from_dir



def bootstrap_metric_ci(
    values: List[float],
    n_bootstraps: int = 1000,
    ci_level: float = 0.95,
    seed: int = 42
) -> Tuple[float, float, float]:
    """
    Computes mean and [lower, upper] percentile bootstrap confidence intervals.
    """
    if not values:
        return 0.0, 0.0, 0.0
    
    rng = random.Random(seed)
    n = len(values)
    boot_means = []
    
    for _ in range(n_bootstraps):
        sample = [rng.choice(values) for _ in range(n)]
        boot_means.append(sum(sample) / n)
        
    boot_means.sort()
    alpha = (1.0 - ci_level) / 2.0
    lower_idx = int(alpha * n_bootstraps)
    upper_idx = int((1.0 - alpha) * n_bootstraps)
    
    mean_val = sum(values) / n
    lower_ci = boot_means[lower_idx]
    upper_ci = boot_means[upper_idx]
    
    return round(mean_val, 4), round(lower_ci, 4), round(upper_ci, 4)


def run_baseline_bootstrap_audit(
    results_dir: str = "eval_results/baseline_phase1",
    benchmark_dev_dir: str = "benchmark/frozen/bioreasonbench_v0.1/dev",
    n_bootstraps: int = 1000,
) -> Dict[str, Any]:
    dev_items = load_benchmark_from_dir(benchmark_dev_dir)
    item_map = {item.item_id: item for item in dev_items}

    models = ["Qwen2.5-7B-Instruct", "Qwen2.5-14B-Instruct", "Qwen2.5-32B-Instruct"]
    audit_summary = {}

    for model_name in models:
        eval_file = Path(results_dir) / f"{model_name}_eval.json"
        if not eval_file.exists():
            continue
        
        with open(eval_file, "r") as f:
            eval_data = json.load(f)
            
        scores = eval_data["individual_scores"]
        preds = eval_data["predictions"]

        composites = [s["composite_score"] for s in scores]
        flaw_accs = [1.0 if s["flaw_detected_binary"] else 0.0 for s in scores]
        crit_fails = [1.0 if s["critical_failure"] else 0.0 for s in scores]
        explanations = [s["explanation_score"] for s in scores]
        corrections = [s["correction_score"] for s in scores]
        calibrations = [s["calibration_score"] for s in scores]
        
        # Difficulty subsets
        adv_scores = [s["composite_score"] for s in scores if item_map.get(s["item_id"]) and item_map[s["item_id"]].difficulty == DifficultyLevel.ADVANCED]
        adv_flaw = [1.0 if s["flaw_detected_binary"] else 0.0 for s in scores if item_map.get(s["item_id"]) and item_map[s["item_id"]].difficulty == DifficultyLevel.ADVANCED]
        
        opp_scores = [s["composite_score"] for s in scores if item_map.get(s["item_id"]) and item_map[s["item_id"]].difficulty == DifficultyLevel.ADVERSARIAL]
        opp_crit = [1.0 if s["critical_failure"] else 0.0 for s in scores if item_map.get(s["item_id"]) and item_map[s["item_id"]].difficulty == DifficultyLevel.ADVERSARIAL]

        # Scientific False Alarm Rate (cases where benchmark is NOT flawed, but model flags an issue)
        valid_cases = [s for s in scores if item_map.get(s["item_id"]) and not item_map[s["item_id"]].flawed_analysis_present]
        false_alarms = [1.0 if not s["flaw_detected_binary"] else 0.0 for s in valid_cases]

        # Compute Bootstrap CIs
        ci_composite = bootstrap_metric_ci(composites, n_bootstraps=n_bootstraps)
        ci_flaw_acc = bootstrap_metric_ci(flaw_accs, n_bootstraps=n_bootstraps)
        ci_crit_fail = bootstrap_metric_ci(crit_fails, n_bootstraps=n_bootstraps)
        ci_explanation = bootstrap_metric_ci(explanations, n_bootstraps=n_bootstraps)
        ci_correction = bootstrap_metric_ci(corrections, n_bootstraps=n_bootstraps)
        ci_calibration = bootstrap_metric_ci(calibrations, n_bootstraps=n_bootstraps)
        ci_adv_score = bootstrap_metric_ci(adv_scores, n_bootstraps=n_bootstraps)
        ci_opp_score = bootstrap_metric_ci(opp_scores, n_bootstraps=n_bootstraps)
        ci_opp_crit = bootstrap_metric_ci(opp_crit, n_bootstraps=n_bootstraps)
        ci_false_alarm = bootstrap_metric_ci(false_alarms, n_bootstraps=n_bootstraps)

        audit_summary[model_name] = {
            "total_items": len(scores),
            "composite_score": {"mean": ci_composite[0], "ci_95": [ci_composite[1], ci_composite[2]]},
            "flaw_detection_accuracy": {"mean": ci_flaw_acc[0], "ci_95": [ci_flaw_acc[1], ci_flaw_acc[2]]},
            "critical_failure_rate": {"mean": ci_crit_fail[0], "ci_95": [ci_crit_fail[1], ci_crit_fail[2]]},
            "scientific_explanation": {"mean": ci_explanation[0], "ci_95": [ci_explanation[1], ci_explanation[2]]},
            "correction_quality": {"mean": ci_correction[0], "ci_95": [ci_correction[1], ci_correction[2]]},
            "uncertainty_calibration": {"mean": ci_calibration[0], "ci_95": [ci_calibration[1], ci_calibration[2]]},
            "advanced_composite": {"mean": ci_adv_score[0], "ci_95": [ci_adv_score[1], ci_adv_score[2]]},
            "adversarial_composite": {"mean": ci_opp_score[0], "ci_95": [ci_opp_score[1], ci_opp_score[2]]},
            "adversarial_critical_failure_rate": {"mean": ci_opp_crit[0], "ci_95": [ci_opp_crit[1], ci_opp_crit[2]]},
            "scientific_false_alarm_rate": {"mean": ci_false_alarm[0], "ci_95": [ci_false_alarm[1], ci_false_alarm[2]]},
        }

    # Save summary
    out_file = Path(results_dir) / "baseline_bootstrap_audit.json"
    with open(out_file, "w") as f:
        json.dump(audit_summary, f, indent=2)

    return audit_summary


if __name__ == "__main__":
    print("Running baseline bootstrap confidence interval audit (B=1,000)...")
    summary = run_baseline_bootstrap_audit()
    print(json.dumps(summary, indent=2))

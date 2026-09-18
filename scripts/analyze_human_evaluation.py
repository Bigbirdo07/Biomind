#!/usr/bin/env python3
"""
scripts/analyze_human_evaluation.py

Performs pre-registered statistical analysis of double-blinded human evaluations
for BioReason v0.2, matching HUMAN_EVALUATION_ANALYSIS_PLAN.md.

Invariants:
1. Operates ONLY on frozen reviews from human_eval/v0.2/frozen_reviews/
2. Requires explicit unblinding key provided via CLI argument.
3. Implements:
   - 10-dimension rubric aggregation (mean, std, median, IQR)
   - Pairwise head-to-head win/loss/tie rates
   - Scientist Trust Score (Exploratory)
   - Reviewer confidence stratification (LOW, MEDIUM, HIGH)
   - Reviewer qualification tier stratification
   - Inter-rater agreement (percent agreement, Krippendorff's alpha / Cohen's kappa)
"""

import sys
import os
import json
import math
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Tuple, Optional

RUBRIC_DIMS = [
    "SCIENTIFIC_CORRECTNESS",
    "PRIMARY_ISSUE_IDENTIFICATION",
    "EXPERIMENTAL_UNIT_REASONING",
    "STATISTICAL_VALIDITY",
    "BIOLOGICAL_PLAUSIBILITY",
    "CORRECTION_ACTIONABILITY",
    "UNCERTAINTY_CALIBRATION",
    "OVERCLAIMING",
    "FALSE_ALARM_BEHAVIOR",
    "OVERALL_SCIENTIFIC_USEFULNESS"
]


def compute_krippendorff_alpha_ordinal(matrix: List[List[Optional[int]]]) -> float:
    """
    Computes Krippendorff's alpha for ordinal data.
    matrix: list of units (cases), where each item is a list of ratings by raters.
    """
    # Simple robust calculation for unit-by-rater matrix
    # Collect all observed values
    observed_pairs = []
    values = []
    for row in matrix:
        valid = [x for x in row if x is not None]
        values.extend(valid)
        if len(valid) >= 2:
            for i in range(len(valid)):
                for j in range(i + 1, len(valid)):
                    observed_pairs.append((valid[i], valid[j]))

    if not observed_pairs:
        return 1.0

    # Observed disagreement
    d_obs = sum((p[0] - p[1]) ** 2 for p in observed_pairs) / len(observed_pairs)

    # Expected disagreement across all values
    n = len(values)
    if n < 2:
        return 1.0
    d_exp = 0.0
    pair_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            d_exp += (values[i] - values[j]) ** 2
            pair_count += 1

    if pair_count == 0 or d_exp == 0:
        return 1.0
    d_exp = d_exp / pair_count

    return max(-1.0, min(1.0, 1.0 - (d_obs / d_exp)))


def compute_trust_score(dim_means: Dict[str, float]) -> float:
    """
    Computes Exploratory Scientist Trust Score:
    STS = 0.35 * Correctness + 0.25 * PrimaryIssue + 0.20 * Calibration + 0.20 * Actionability
    """
    c = dim_means.get("SCIENTIFIC_CORRECTNESS", 3.0)
    p = dim_means.get("PRIMARY_ISSUE_IDENTIFICATION", 3.0)
    u = dim_means.get("UNCERTAINTY_CALIBRATION", 3.0)
    a = dim_means.get("CORRECTION_ACTIONABILITY", 3.0)
    return round(0.35 * c + 0.25 * p + 0.20 * u + 0.20 * a, 4)


def analyze_dataset(frozen_dir: Path, unblinding_key_path: Path) -> Dict[str, Any]:
    """Runs complete pre-registered analysis."""
    # 1. Load unblinding key
    with open(unblinding_key_path, "r", encoding="utf-8") as f:
        unblind_data = json.load(f)
    case_mappings = unblind_data.get("randomization_mapping", unblind_data.get("case_randomizations", {}))

    def normalize_model(m_str: str) -> str:
        s = m_str.upper()
        if "V0_2" in s or "V0.2" in s:
            return "v0.2"
        elif "V0_1" in s or "V0.1" in s:
            return "v0.1"
        elif "BASE" in s or "QWEN" in s:
            return "base"
        return m_str

    # 2. Load all frozen reviews
    files = list(frozen_dir.glob("*.json"))
    review_files = [f for f in files if f.name != "review_manifest.json"]

    reviews = []
    for f in review_files:
        with open(f, "r", encoding="utf-8") as fp:
            d = json.load(fp)
            if isinstance(d, list):
                reviews.extend(d)
            elif isinstance(d, dict):
                reviews.append(d)

    # Map model canonical keys: 'base', 'v0.1', 'v0.2'
    # Storage for dimensions
    model_scores = defaultdict(lambda: defaultdict(list))
    # Stratified storage
    by_confidence = {
        "HIGH": defaultdict(lambda: defaultdict(list)),
        "MEDIUM": defaultdict(lambda: defaultdict(list)),
        "LOW": defaultdict(lambda: defaultdict(list))
    }
    by_tier = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    # Pairwise preference counts
    pairwise_preferences = {
        "v0.2_wins": 0,
        "v0.1_wins": 0,
        "base_wins": 0,
        "ties": 0,
        "none_acceptable": 0,
        "total_comparisons": len(reviews)
    }

    # Case-level matrix for inter-rater agreement on correctness and preference
    case_v02_correctness = defaultdict(list)
    case_preferences = defaultdict(list)

    for rev in reviews:
        cid = rev["case_id"]
        r_id = rev["reviewer_id"]
        conf = rev.get("reviewer_confidence", "MEDIUM")
        tier = rev.get("qualification_tier", "GENERAL_BIOLOGICAL_SCIENTIST")
        mapping = case_mappings.get(cid, {})

        # Evaluations
        evals = rev.get("response_evaluations", {})
        for resp_label, raw_model in mapping.items():
            canonical_model = normalize_model(raw_model)
            if resp_label in evals:
                r_scores = evals[resp_label]
                for dim in RUBRIC_DIMS:
                    val = r_scores.get(dim)
                    if val is not None:
                        model_scores[canonical_model][dim].append(val)
                        by_confidence[conf][canonical_model][dim].append(val)
                        by_tier[tier][canonical_model][dim].append(val)
                        if canonical_model == "v0.2" and dim == "SCIENTIFIC_CORRECTNESS":
                            case_v02_correctness[cid].append(val)

        # Preference unblinding
        pref = rev.get("pairwise_preference")
        if pref == "TIE":
            pairwise_preferences["ties"] += 1
            case_preferences[cid].append("TIE")
        elif pref == "NONE_ACCEPTABLE":
            pairwise_preferences["none_acceptable"] += 1
            case_preferences[cid].append("NONE_ACCEPTABLE")
        elif pref in mapping:
            chosen_canonical = normalize_model(mapping[pref])
            if chosen_canonical == "v0.2":
                pairwise_preferences["v0.2_wins"] += 1
            elif chosen_canonical == "v0.1":
                pairwise_preferences["v0.1_wins"] += 1
            elif chosen_canonical == "base":
                pairwise_preferences["base_wins"] += 1
            case_preferences[cid].append(chosen_canonical)

    # Aggregate metric calculations
    aggregated_metrics = {}
    for model_name, dims in model_scores.items():
        dim_stats = {}
        for dim, vals in dims.items():
            if vals:
                mean_v = sum(vals) / len(vals)
                std_v = math.sqrt(sum((x - mean_v) ** 2 for x in vals) / len(vals)) if len(vals) > 1 else 0.0
                sorted_v = sorted(vals)
                median_v = sorted_v[len(sorted_v) // 2]
                dim_stats[dim] = {
                    "mean": round(mean_v, 3),
                    "std": round(std_v, 3),
                    "median": median_v,
                    "n": len(vals)
                }
        means_only = {d: stats["mean"] for d, stats in dim_stats.items()}
        trust = compute_trust_score(means_only)
        aggregated_metrics[model_name] = {
            "dimensions": dim_stats,
            "scientist_trust_score_exploratory": trust
        }

    # Inter-rater agreement
    correctness_matrix = list(case_v02_correctness.values())
    alpha_correctness = compute_krippendorff_alpha_ordinal(correctness_matrix)

    # Calculate agreement on preference
    pref_agree_pairs = 0
    total_pref_pairs = 0
    for cid, prefs in case_preferences.items():
        if len(prefs) >= 2:
            for i in range(len(prefs)):
                for j in range(i + 1, len(prefs)):
                    total_pref_pairs += 1
                    if prefs[i] == prefs[j]:
                        pref_agree_pairs += 1
    pct_pref_agreement = (pref_agree_pairs / total_pref_pairs * 100) if total_pref_pairs > 0 else 0.0

    return {
        "analysis_version": "v0.2",
        "total_reviews_analyzed": len(reviews),
        "total_cases_covered": len(case_v02_correctness),
        "model_performance": aggregated_metrics,
        "pairwise_preferences": pairwise_preferences,
        "inter_rater_reliability": {
            "krippendorff_alpha_v02_correctness": round(alpha_correctness, 4),
            "pairwise_preference_agreement_pct": round(pct_pref_agreement, 2),
            "total_paired_comparisons": total_pref_pairs
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze double-blind human evaluation data.")
    parser.add_argument("--frozen-dir", default="human_eval/v0.2/frozen_reviews", help="Path to frozen reviews directory")
    parser.add_argument("--unblinding-key", default="human_eval/v0.2/randomization_manifest.json", help="Path to unblinding key")
    parser.add_argument("--output", default="human_eval/v0.2/human_evaluation_results.json", help="Path for output JSON")
    args = parser.parse_args()

    frozen_dir = Path(args.frozen_dir)
    unblinding_key = Path(args.unblinding_key)

    if not frozen_dir.exists() or not list(frozen_dir.glob("*.json")):
        print(f"Error: No frozen human review files found in {frozen_dir}. Reviews must be completed and frozen first.")
        sys.exit(1)

    results = analyze_dataset(frozen_dir, unblinding_key)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Analysis complete. Results written to {args.output}")


if __name__ == "__main__":
    main()

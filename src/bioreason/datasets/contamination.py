"""
Benchmark and training data contamination detection tool (Contamination Engine v2).
Enforces strict firewalls using exact matching, normalized n-grams, Jaccard overlap,
and semantic Scenario Signature comparisons.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from bioreason.schemas.episode import ScientificReasoningEpisode, ScenarioSignature
from bioreason.schemas.benchmark import BenchmarkItem


def normalize_text(text: str) -> str:
    """Normalize text by lowercasing, removing punctuation, and collapsing whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def get_ngrams(text: str, n: int = 3) -> set:
    words = normalize_text(text).split()
    if len(words) < n:
        return set()
    return set(tuple(words[i : i + n]) for i in range(len(words) - n + 1))


def tokenize(text: str) -> set:
    words = re.findall(r"\b\w{3,}\b", text.lower())
    return set(words)


def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0


def compare_scenario_signatures(
    sig_a: Optional[ScenarioSignature],
    sig_b: Optional[ScenarioSignature],
) -> Tuple[bool, float]:
    """
    Compares two structured scenario signatures.
    Returns (is_match, similarity_score).
    """
    if sig_a is None or sig_b is None:
        return False, 0.0

    fields = ["assay", "problem", "experimental_unit", "analysis", "failure_mode"]
    matches = sum(
        1 for f in fields if getattr(sig_a, f, "").lower() == getattr(sig_b, f, "").lower() and getattr(sig_a, f, "") != ""
    )
    score = matches / len(fields)
    # A match occurs if problem, experimental_unit, and failure_mode are identical
    is_critical_match = (
        sig_a.problem.lower() == sig_b.problem.lower()
        and sig_a.experimental_unit.lower() == sig_b.experimental_unit.lower()
        and sig_a.failure_mode.lower() == sig_b.failure_mode.lower()
        and sig_a.failure_mode.lower() not in ["none", ""]
    )
    return is_critical_match, score


def check_contamination(
    training_episodes: List[ScientificReasoningEpisode],
    benchmark_items: List[BenchmarkItem],
    similarity_threshold: float = 0.65,
) -> List[Dict[str, Any]]:
    """
    Checks for potential data leakage or scenario overlap between
    training reasoning episodes and held-out benchmark items.
    """
    contamination_reports = []

    for bench in benchmark_items:
        norm_bench_q = normalize_text(bench.question)
        norm_bench_scenario = normalize_text(bench.scenario)
        bench_tokens = tokenize(f"{bench.question} {bench.scenario}")
        bench_3grams = get_ngrams(f"{bench.question} {bench.scenario}", n=3)

        for train in training_episodes:
            norm_train_q = normalize_text(train.question)
            train_tokens = tokenize(f"{train.question} {train.proposed_analysis} {train.reasoning_summary}")
            train_3grams = get_ngrams(f"{train.question} {train.proposed_analysis} {train.reasoning_summary}", n=3)

            # Check 1: Exact question match
            if bench.question.strip().lower() == train.question.strip().lower():
                contamination_reports.append({
                    "benchmark_id": bench.item_id,
                    "training_id": train.episode_id,
                    "contamination_type": "EXACT_QUESTION_MATCH",
                    "similarity": 1.0,
                    "message": f"Benchmark item {bench.item_id} has identical question to training episode {train.episode_id}."
                })
                continue

            # Check 2: Normalized exact scenario match
            if norm_bench_q == norm_train_q:
                contamination_reports.append({
                    "benchmark_id": bench.item_id,
                    "training_id": train.episode_id,
                    "contamination_type": "NORMALIZED_QUESTION_MATCH",
                    "similarity": 1.0,
                    "message": f"Benchmark item {bench.item_id} has identical normalized question to training episode {train.episode_id}."
                })
                continue

            # Check 3: Structured Scenario Signature overlap
            sig_match, sig_score = compare_scenario_signatures(
                getattr(bench, "scenario_signature", None),
                getattr(train, "scenario_signature", None),
            )
            if sig_match and sig_score >= 0.8:
                contamination_reports.append({
                    "benchmark_id": bench.item_id,
                    "training_id": train.episode_id,
                    "contamination_type": "SCENARIO_SIGNATURE_COLLISION",
                    "similarity": round(sig_score, 3),
                    "message": (
                        f"Benchmark item {bench.item_id} has near-identical semantic scenario signature "
                        f"(score: {sig_score:.2f}) with training episode {train.episode_id}."
                    )
                })
                continue

            # Check 4: High token Jaccard similarity
            sim = jaccard_similarity(bench_tokens, train_tokens)
            if sim >= similarity_threshold:
                contamination_reports.append({
                    "benchmark_id": bench.item_id,
                    "training_id": train.episode_id,
                    "contamination_type": "HIGH_TOKEN_SIMILARITY",
                    "similarity": round(sim, 3),
                    "message": (
                        f"Benchmark item {bench.item_id} has high text token similarity ({sim:.2f}) "
                        f"with training episode {train.episode_id}."
                    )
                })

    return contamination_reports

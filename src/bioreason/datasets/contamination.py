"""
Benchmark and training data contamination detection tool.
"""

import re
from typing import List, Dict, Any, Tuple
from bioreason.schemas.episode import ScientificReasoningEpisode
from bioreason.schemas.benchmark import BenchmarkItem


def tokenize(text: str) -> set:
    words = re.findall(r"\b\w{3,}\b", text.lower())
    return set(words)


def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0


def check_contamination(
    training_episodes: List[ScientificReasoningEpisode],
    benchmark_items: List[BenchmarkItem],
    similarity_threshold: float = 0.65,
) -> List[Dict[str, Any]]:
    """
    Checks for potential data leakage or question/scenario overlap between
    training reasoning episodes and held-out benchmark items.
    """
    contamination_reports = []

    for bench in benchmark_items:
        bench_tokens = tokenize(f"{bench.question} {bench.scenario}")
        for train in training_episodes:
            train_tokens = tokenize(f"{train.question} {train.proposed_analysis} {train.reasoning_summary}")
            
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

            # Check 2: High token overlap (Jaccard similarity)
            sim = jaccard_similarity(bench_tokens, train_tokens)
            if sim >= similarity_threshold:
                contamination_reports.append({
                    "benchmark_id": bench.item_id,
                    "training_id": train.episode_id,
                    "contamination_type": "HIGH_SCENARIO_SIMILARITY",
                    "similarity": round(sim, 3),
                    "message": (
                        f"Benchmark item {bench.item_id} has high text/scenario similarity ({sim:.2f}) "
                        f"with training episode {train.episode_id}."
                    )
                })

    return contamination_reports

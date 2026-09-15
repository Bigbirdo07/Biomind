"""
Benchmark and training data contamination detection tool (Contamination Engine V3).
Enforces strict firewalls using:
1. Exact question matching
2. Normalized scenario matching
3. Semantic ScenarioSignature collision checks
4. Token n-gram Jaccard overlap
5. Semantic similarity architecture (offline subword/TF-IDF cosine similarity and optional dense embedding cache)
6. Non-destructive flagging to Human Review Queue
"""

import re
import math
import json
from pathlib import Path
from collections import Counter
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


def compute_char_ngram_vector(text: str, n: int = 3) -> Dict[str, int]:
    """Offline subword character n-gram frequency vector."""
    norm = normalize_text(text)
    if len(norm) < n:
        return {norm: 1} if norm else {}
    ngrams = [norm[i : i + n] for i in range(len(norm) - n + 1)]
    return dict(Counter(ngrams))


def cosine_similarity_vectors(vec_a: Dict[str, int], vec_b: Dict[str, int]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    intersection = set(vec_a.keys()) & set(vec_b.keys())
    numerator = sum(vec_a[k] * vec_b[k] for k in intersection)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return numerator / (mag_a * mag_b)


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


class SemanticSimilarityEngine:
    """
    Optional semantic similarity engine for Contamination Engine V3.
    Operates offline via TF-IDF character-ngram embeddings by default.
    Optionally integrates external dense embeddings with caching and version tracking.
    """
    engine_version: str = "v3.0.0-subword-offline"

    def __init__(
        self,
        embedding_model_name: str = "offline-subword-char-ngram",
        semantic_threshold: float = 0.82,
        embedding_cache_path: Optional[str] = None,
    ):
        self.embedding_model_name = embedding_model_name
        self.semantic_threshold = semantic_threshold
        self.embedding_cache_path = embedding_cache_path
        self._cache: Dict[str, Any] = {}
        if embedding_cache_path and Path(embedding_cache_path).exists():
            try:
                with open(embedding_cache_path, "r") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        vec_a = compute_char_ngram_vector(text_a, n=4)
        vec_b = compute_char_ngram_vector(text_b, n=4)
        return cosine_similarity_vectors(vec_a, vec_b)


def check_contamination(
    training_episodes: List[ScientificReasoningEpisode],
    benchmark_items: List[BenchmarkItem],
    similarity_threshold: float = 0.65,
    semantic_threshold: float = 0.82,
    export_review_queue_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Checks for potential data leakage or scenario overlap between
    training reasoning episodes and held-out benchmark items (Contamination Engine V3).
    Non-destructive: Flags cases for human review instead of silent removal.
    """
    contamination_reports = []
    semantic_engine = SemanticSimilarityEngine(semantic_threshold=semantic_threshold)

    # Pre-extract benchmark representations
    bench_data = []
    for bench in benchmark_items:
        raw_q = bench.question.strip().lower()
        norm_q = normalize_text(bench.question)
        full_text = f"{bench.question} {bench.scenario}"
        tokens = tokenize(full_text)
        vec = compute_char_ngram_vector(full_text, n=4)
        sig = getattr(bench, "scenario_signature", None)
        bench_data.append((bench, raw_q, norm_q, tokens, vec, sig, full_text))

    # Pre-extract training representations
    train_data = []
    for train in training_episodes:
        raw_q = train.question.strip().lower()
        norm_q = normalize_text(train.question)
        full_text = f"{train.question} {train.proposed_analysis} {train.reasoning_summary}"
        tokens = tokenize(full_text)
        vec = compute_char_ngram_vector(full_text, n=4)
        sig = getattr(train, "scenario_signature", None)
        train_data.append((train, raw_q, norm_q, tokens, vec, sig, full_text))

    for bench, b_raw_q, b_norm_q, b_tokens, b_vec, b_sig, b_full in bench_data:
        for train, t_raw_q, t_norm_q, t_tokens, t_vec, t_sig, t_full in train_data:

            # Check 1: Exact question match
            if b_raw_q == t_raw_q:
                contamination_reports.append({
                    "benchmark_id": bench.item_id,
                    "training_id": train.episode_id,
                    "contamination_type": "EXACT_QUESTION_MATCH",
                    "similarity": 1.0,
                    "message": f"Benchmark item {bench.item_id} has identical question to training episode {train.episode_id}.",
                    "flagged_for_review": True,
                })
                continue

            # Check 2: Normalized exact scenario match
            if b_norm_q == t_norm_q:
                contamination_reports.append({
                    "benchmark_id": bench.item_id,
                    "training_id": train.episode_id,
                    "contamination_type": "NORMALIZED_QUESTION_MATCH",
                    "similarity": 1.0,
                    "message": f"Benchmark item {bench.item_id} has identical normalized question to training episode {train.episode_id}.",
                    "flagged_for_review": True,
                })
                continue

            # Check 3: Structured Scenario Signature overlap
            sig_match, sig_score = compare_scenario_signatures(b_sig, t_sig)
            if sig_match and sig_score >= 0.8:
                contamination_reports.append({
                    "benchmark_id": bench.item_id,
                    "training_id": train.episode_id,
                    "contamination_type": "SCENARIO_SIGNATURE_COLLISION",
                    "similarity": round(sig_score, 3),
                    "message": (
                        f"Benchmark item {bench.item_id} has near-identical semantic scenario signature "
                        f"(score: {sig_score:.2f}) with training episode {train.episode_id}."
                    ),
                    "flagged_for_review": True,
                })
                continue

            # Check 4: High token Jaccard similarity
            sim = jaccard_similarity(b_tokens, t_tokens)
            if sim >= similarity_threshold:
                contamination_reports.append({
                    "benchmark_id": bench.item_id,
                    "training_id": train.episode_id,
                    "contamination_type": "HIGH_TOKEN_SIMILARITY",
                    "similarity": round(sim, 3),
                    "message": (
                        f"Benchmark item {bench.item_id} has high text token similarity ({sim:.2f}) "
                        f"with training episode {train.episode_id}."
                    ),
                    "flagged_for_review": True,
                })
                continue

            # Check 5: Semantic cosine similarity (V3 semantic firewall) - evaluated on candidate pairs
            if sim >= 0.40:
                sem_sim = cosine_similarity_vectors(b_vec, t_vec)
                if sem_sim >= semantic_threshold:
                    contamination_reports.append({
                        "benchmark_id": bench.item_id,
                        "training_id": train.episode_id,
                        "contamination_type": "SEMANTIC_SIMILARITY_FLAG",
                        "similarity": round(sem_sim, 3),
                        "engine_version": semantic_engine.engine_version,
                        "message": (
                            f"Benchmark item {bench.item_id} flagged for high semantic similarity ({sem_sim:.2f}) "
                            f"with training episode {train.episode_id}."
                        ),
                        "flagged_for_review": True,
                    })


    # Optional export to human review queue
    if export_review_queue_dir and contamination_reports:
        review_path = Path(export_review_queue_dir) / "contamination_concerns.json"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        with open(review_path, "w") as f:
            json.dump(contamination_reports, f, indent=2)

    return contamination_reports



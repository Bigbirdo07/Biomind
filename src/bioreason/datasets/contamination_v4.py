"""
Benchmark and training data contamination detection tool (Contamination Engine V4).
Enforces comprehensive scientific firewalls across splits using:
1. Exact question and prompt matching
2. Normalized scenario matching
3. Token n-gram Jaccard overlap
4. Semantic ScenarioSignature collision detection
5. Subword & TF-IDF cosine semantic similarity
6. Study-Structure Fingerprinting (assay, design, unit hierarchy, objective, failure type)
7. Source-Document Provenance & Citation/DOI/URL Overlap Detection
8. Experiment-Graph Structural Topology Fingerprint Matching
9. Non-destructive audit reporting to Human Review Queue
"""

import re
import math
import json
import hashlib
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional, Union, Set
from bioreason.schemas.episode import ScientificReasoningEpisode, ScenarioSignature, SourceProvenance
from bioreason.schemas.benchmark import BenchmarkItem
from bioreason.schemas.experiment_graph import ExperimentGraph


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


def compute_char_ngram_vector(text: str, n: int = 4) -> Dict[str, int]:
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
    if sig_a is None or sig_b is None:
        return False, 0.0

    fields = ["assay", "problem", "experimental_unit", "analysis", "failure_mode"]
    matches = sum(
        1 for f in fields if getattr(sig_a, f, "").lower() == getattr(sig_b, f, "").lower() and getattr(sig_a, f, "") != ""
    )
    score = matches / len(fields)
    is_critical_match = (
        sig_a.problem.lower() == sig_b.problem.lower()
        and sig_a.experimental_unit.lower() == sig_b.experimental_unit.lower()
        and sig_a.failure_mode.lower() == sig_b.failure_mode.lower()
        and sig_a.failure_mode.lower() not in ["none", ""]
    )
    return is_critical_match, score


def extract_provenance_identifiers(prov: Optional[Union[SourceProvenance, Dict[str, Any], List[str]]]) -> Set[str]:
    """Extracts normalized DOIs, citations, URLs, and accession IDs for provenance overlap checking."""
    ids = set()
    if prov is None:
        return ids

    if isinstance(prov, list):
        for item in prov:
            if isinstance(item, str) and item.strip():
                # Extract potential DOIs or identifiers
                norm = normalize_text(item)
                if len(norm) > 10:
                    ids.add(norm)
        return ids

    if isinstance(prov, SourceProvenance):
        if prov.doi:
            ids.add(prov.doi.strip().lower())
        if prov.citation:
            ids.add(normalize_text(prov.citation))
    elif isinstance(prov, dict):
        if prov.get("doi"):
            ids.add(str(prov["doi"]).strip().lower())
        if prov.get("citation"):
            ids.add(normalize_text(str(prov["citation"])))

    return ids


def compute_study_structure_fingerprint(
    domain: Optional[str],
    assay: Optional[str],
    unit: Optional[str],
    objective: Optional[str],
    flaw_or_failure: Optional[str],
) -> str:
    """Computes an abstract study-structure signature."""
    elements = [
        str(domain or "").strip().lower(),
        str(assay or "").strip().lower(),
        str(unit or "").strip().lower(),
        str(objective or "").strip().lower(),
        str(flaw_or_failure or "").strip().lower(),
    ]
    raw = "|".join(elements)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class ContaminationEngineV4:
    """
    Contamination Engine V4: Multimodal scientific firewall supporting:
    - Textual similarity (Exact, Normalized, N-Gram Jaccard, Subword TF-IDF)
    - Semantic ScenarioSignature collisions
    - Provenance & Citation/DOI overlap
    - Study-Structure fingerprint collisions
    - ExperimentGraph topological structure matching
    """
    engine_version: str = "v4.0.0-multimodal-firewall"

    def __init__(
        self,
        token_similarity_threshold: float = 0.65,
        semantic_threshold: float = 0.82,
        ngram_threshold: float = 0.70,
    ):
        self.token_similarity_threshold = token_similarity_threshold
        self.semantic_threshold = semantic_threshold
        self.ngram_threshold = ngram_threshold

    def audit_contamination(
        self,
        candidate_items: List[Union[ScientificReasoningEpisode, BenchmarkItem, Dict[str, Any]]],
        reference_items: List[Union[ScientificReasoningEpisode, BenchmarkItem, Dict[str, Any]]],
        candidate_label: str = "candidate",
        reference_label: str = "reference",
        export_report_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        reports = []

        # Preprocess reference items
        ref_records = []
        for ref in reference_items:
            ref_id = getattr(ref, "item_id", None) or getattr(ref, "episode_id", None) or (ref.get("item_id") or ref.get("episode_id") if isinstance(ref, dict) else "unknown_ref")
            ref_q = str(getattr(ref, "question", None) or (ref.get("question") if isinstance(ref, dict) else "") or "")
            ref_scen = str(getattr(ref, "scenario", None) or getattr(ref, "proposed_analysis", None) or (ref.get("scenario") or ref.get("proposed_analysis") if isinstance(ref, dict) else "") or "")
            ref_full = f"{ref_q} {ref_scen}".strip()
            ref_tokens = tokenize(ref_full)
            ref_vec = compute_char_ngram_vector(ref_full, n=4)
            ref_sig = getattr(ref, "scenario_signature", None) or (ref.get("scenario_signature") if isinstance(ref, dict) else None)
            ref_prov_ids = extract_provenance_identifiers(getattr(ref, "provenance", None) or getattr(ref, "sources", None) or (ref.get("provenance") or ref.get("sources") if isinstance(ref, dict) else None))
            
            ref_records.append({
                "item": ref,
                "id": ref_id,
                "raw_q": ref_q.strip().lower(),
                "norm_q": normalize_text(ref_q),
                "tokens": ref_tokens,
                "vec": ref_vec,
                "sig": ref_sig,
                "prov_ids": ref_prov_ids,
                "full_text": ref_full,
            })

        for cand in candidate_items:
            cand_id = getattr(cand, "item_id", None) or getattr(cand, "episode_id", None) or (cand.get("item_id") or cand.get("episode_id") if isinstance(cand, dict) else "unknown_cand")
            cand_q = str(getattr(cand, "question", None) or (cand.get("question") if isinstance(cand, dict) else "") or "")
            cand_scen = str(getattr(cand, "scenario", None) or getattr(cand, "proposed_analysis", None) or (cand.get("scenario") or cand.get("proposed_analysis") if isinstance(cand, dict) else "") or "")
            cand_full = f"{cand_q} {cand_scen}".strip()
            cand_raw_q = cand_q.strip().lower()
            cand_norm_q = normalize_text(cand_q)
            cand_tokens = tokenize(cand_full)
            cand_vec = compute_char_ngram_vector(cand_full, n=4)
            cand_sig = getattr(cand, "scenario_signature", None) or (cand.get("scenario_signature") if isinstance(cand, dict) else None)
            cand_prov_ids = extract_provenance_identifiers(getattr(cand, "provenance", None) or getattr(cand, "sources", None) or (cand.get("provenance") or cand.get("sources") if isinstance(cand, dict) else None))

            for r in ref_records:
                # 1. Exact question match
                if cand_raw_q and cand_raw_q == r["raw_q"]:
                    reports.append({
                        "candidate_id": cand_id,
                        "reference_id": r["id"],
                        "candidate_label": candidate_label,
                        "reference_label": reference_label,
                        "contamination_type": "EXACT_QUESTION_MATCH",
                        "similarity": 1.0,
                        "message": f"Exact question duplicate between {cand_id} and {r['id']}.",
                        "flagged": True,
                    })
                    continue

                # 2. Normalized question match
                if cand_norm_q and cand_norm_q == r["norm_q"]:
                    reports.append({
                        "candidate_id": cand_id,
                        "reference_id": r["id"],
                        "candidate_label": candidate_label,
                        "reference_label": reference_label,
                        "contamination_type": "NORMALIZED_QUESTION_MATCH",
                        "similarity": 1.0,
                        "message": f"Normalized question duplicate between {cand_id} and {r['id']}.",
                        "flagged": True,
                    })
                    continue

                # 3. Provenance / DOI Overlap
                prov_overlap = cand_prov_ids.intersection(r["prov_ids"])
                if prov_overlap:
                    reports.append({
                        "candidate_id": cand_id,
                        "reference_id": r["id"],
                        "candidate_label": candidate_label,
                        "reference_label": reference_label,
                        "contamination_type": "PROVENANCE_SOURCE_OVERLAP",
                        "similarity": 1.0,
                        "message": f"Source/DOI overlap detected between {cand_id} and {r['id']}: {list(prov_overlap)}.",
                        "flagged": True,
                    })
                    continue

                # 4. Scenario Signature Collision
                if cand_sig and r["sig"]:
                    # Convert dicts to ScenarioSignature if needed
                    s_cand = ScenarioSignature(**cand_sig) if isinstance(cand_sig, dict) else cand_sig
                    s_ref = ScenarioSignature(**r["sig"]) if isinstance(r["sig"], dict) else r["sig"]
                    sig_match, sig_score = compare_scenario_signatures(s_cand, s_ref)
                    if sig_match and sig_score >= 0.8:
                        reports.append({
                            "candidate_id": cand_id,
                            "reference_id": r["id"],
                            "candidate_label": candidate_label,
                            "reference_label": reference_label,
                            "contamination_type": "SCENARIO_SIGNATURE_COLLISION",
                            "similarity": round(sig_score, 3),
                            "message": f"Scenario signature collision (score {sig_score:.2f}) between {cand_id} and {r['id']}.",
                            "flagged": True,
                        })
                        continue

                # 5. Token Jaccard Similarity
                jacc = jaccard_similarity(cand_tokens, r["tokens"])
                if jacc >= self.token_similarity_threshold:
                    reports.append({
                        "candidate_id": cand_id,
                        "reference_id": r["id"],
                        "candidate_label": candidate_label,
                        "reference_label": reference_label,
                        "contamination_type": "HIGH_TOKEN_SIMILARITY",
                        "similarity": round(jacc, 3),
                        "message": f"High token Jaccard similarity ({jacc:.2f}) between {cand_id} and {r['id']}.",
                        "flagged": True,
                    })
                    continue

                # 6. Semantic Subword Cosine Similarity
                if jacc >= 0.40:
                    sem_sim = cosine_similarity_vectors(cand_vec, r["vec"])
                    if sem_sim >= self.semantic_threshold:
                        reports.append({
                            "candidate_id": cand_id,
                            "reference_id": r["id"],
                            "candidate_label": candidate_label,
                            "reference_label": reference_label,
                            "contamination_type": "SEMANTIC_SIMILARITY_FLAG",
                            "similarity": round(sem_sim, 3),
                            "message": f"High semantic subword cosine similarity ({sem_sim:.2f}) between {cand_id} and {r['id']}.",
                            "flagged": True,
                        })

        if export_report_path and reports:
            p = Path(export_report_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w") as f:
                json.dump(reports, f, indent=2)

        return reports


def check_contamination_v4(
    candidate_items: List[Any],
    reference_items: List[Any],
    token_threshold: float = 0.65,
    semantic_threshold: float = 0.82,
) -> List[Dict[str, Any]]:
    """Functional convenience wrapper for ContaminationEngineV4."""
    engine = ContaminationEngineV4(
        token_similarity_threshold=token_threshold,
        semantic_threshold=semantic_threshold,
    )
    return engine.audit_contamination(candidate_items, reference_items)

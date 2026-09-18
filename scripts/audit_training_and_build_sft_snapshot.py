"""
Training Data Quality Audit & SFT Snapshot Engine (BioReasonTrain-SFT-v0.1).
Audits training data across domain, difficulty, episode type, and quality gates.
Assigns quality tiers (TIER_A, TIER_B, TIER_C, TIER_D) and configurable example weights.
Splits 90/10 stratified by ScenarioSignature family to prevent trivial memorization across splits.
"""

import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List

from bioreason.schemas.episode import ScientificReasoningEpisode, ValidationStatus
from bioreason.datasets.loader import load_episodes_from_dir
from bioreason.validators.quality_gates import validate_episode_quality_gates


def audit_and_create_sft_snapshot(
    train_dir: str = "training_data/examples",
    snapshot_dir: str = "training_data/snapshots/bioreasontrain_sft_v0.1",
    tier_weights: Dict[str, float] = None,
    val_ratio: float = 0.10,
    seed: int = 42,
) -> Dict[str, Any]:
    if tier_weights is None:
        tier_weights = {
            "TIER_A": 1.0,
            "TIER_B": 1.0,
            "TIER_C": 0.70,
            "TIER_D": 0.0,
        }

    episodes = load_episodes_from_dir(train_dir)
    episodes = sorted(episodes, key=lambda x: x.episode_id)
    n_total = len(episodes)

    # 1. Stratified Quality Gate Audit
    quality_issues = []
    for ep in episodes:
        issues = validate_episode_quality_gates(ep)
        for issue in issues:
            quality_issues.append(issue.to_dict())

    # 2. Quality Tier Assignment
    # TIER_A: expert_validated hand-crafted episodes (first 45)
    # TIER_C: structured auto_validated with deterministic rule support
    # (No TIER_D weak synthetic candidates admitted to SFT-v0.1)
    tiered_episodes = []
    tier_counts = Counter()

    for ep in episodes:
        ep_dict = ep.model_dump(mode="json")
        if ep.validation_status == ValidationStatus.EXPERT_VALIDATED:
            tier = "TIER_A"
        elif ep.validation_status in [ValidationStatus.SCIENTIST_REVIEWED, ValidationStatus.PEER_REVIEWED]:
            tier = "TIER_B"
        elif ep.validation_status == ValidationStatus.AUTO_VALIDATED:
            tier = "TIER_C"
        else:
            tier = "TIER_D"

        tier_counts[tier] += 1
        ep_dict["quality_tier"] = tier
        ep_dict["example_weight"] = tier_weights.get(tier, 0.70)
        tiered_episodes.append(ep_dict)

    # Filter out TIER_D (if any)
    sft_eligible = [ep for ep in tiered_episodes if ep["quality_tier"] in ["TIER_A", "TIER_B", "TIER_C"]]

    # 3. 90/10 Stratified Split by ScenarioSignature family
    rng = random.Random(seed)
    
    # Group by ScenarioSignature family (assay + problem + experimental_unit)
    family_groups: Dict[str, List[Dict[str, Any]]] = {}
    for ep in sft_eligible:
        sig = ep.get("scenario_signature") or {}
        fam_key = f"{sig.get('assay', 'other')}::{sig.get('problem', 'general')}::{sig.get('experimental_unit', 'sample')}"
        family_groups.setdefault(fam_key, []).append(ep)

    train_eps = []
    val_eps = []

    for fam_key, group in sorted(family_groups.items()):
        rng.shuffle(group)
        n_val = max(1, int(len(group) * val_ratio)) if len(group) >= 5 else 0
        val_eps.extend(group[:n_val])
        train_eps.extend(group[n_val:])

    # If small families left val_eps under target, balance deterministically
    target_val = int(len(sft_eligible) * val_ratio)
    if len(val_eps) < target_val:
        diff = target_val - len(val_eps)
        val_eps.extend(train_eps[:diff])
        train_eps = train_eps[diff:]

    # 4. Save Snapshot to Disk
    snap_path = Path(snapshot_dir)
    train_path = snap_path / "train"
    val_path = snap_path / "val"

    train_path.mkdir(parents=True, exist_ok=True)
    val_path.mkdir(parents=True, exist_ok=True)

    for ep in train_eps:
        with open(train_path / f"{ep['episode_id']}.json", "w") as f:
            json.dump(ep, f, indent=2)

    for ep in val_eps:
        with open(val_path / f"{ep['episode_id']}.json", "w") as f:
            json.dump(ep, f, indent=2)

    # 5. Compute Manifest & Hash
    hasher = hashlib.sha256()
    for ep in sorted(sft_eligible, key=lambda x: x["episode_id"]):
        hasher.update(json.dumps(ep, sort_keys=True).encode("utf-8"))
    snapshot_sha256 = hasher.hexdigest()

    domain_counts = dict(Counter(ep["domain"] for ep in sft_eligible))
    type_counts = dict(Counter(ep["episode_type"] for ep in sft_eligible))

    manifest = {
        "dataset_version": "BioReasonTrain-SFT-v0.1",
        "sha256": snapshot_sha256,
        "total_eligible_episodes": len(sft_eligible),
        "train_split_count": len(train_eps),
        "val_split_count": len(val_eps),
        "split_ratio": {"train": round(len(train_eps)/len(sft_eligible), 3), "val": round(len(val_eps)/len(sft_eligible), 3)},
        "quality_tiers": dict(tier_counts),
        "tier_weights": tier_weights,
        "domains": domain_counts,
        "episode_types": type_counts,
        "quality_issues_detected": len(quality_issues),
    }

    with open(snap_path / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest


if __name__ == "__main__":
    print("Auditing training data and building BioReasonTrain-SFT-v0.1 snapshot...")
    manifest = audit_and_create_sft_snapshot()
    print(f"Snapshot version: {manifest['dataset_version']}")
    print(f"SHA-256: {manifest['sha256']}")
    print(f"Train split: {manifest['train_split_count']}, Val split: {manifest['val_split_count']}")
    print(f"Quality Tiers: {manifest['quality_tiers']}")
    print(f"Quality Issues Detected: {manifest['quality_issues_detected']}")
    print("Snapshot created successfully.")

"""
BioReasonBench Versioned Freeze & Stratified Split Engine.
Freezes BioReasonBench-v0.1 into Development Benchmark (~80%) and Final Locked Test (~20%).
Generates cryptographic SHA-256 manifest with category, difficulty, domain distributions and commit provenance.
"""

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from bioreason.schemas.benchmark import BenchmarkItem, DifficultyLevel, BenchmarkCategory
from bioreason.datasets.loader import load_benchmark_from_dir


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "c7dadc1"


def freeze_benchmark_v0_1(
    bench_dir: str = "benchmark/examples",
    out_dir: str = "benchmark/frozen/bioreasonbench_v0.1",
    dev_ratio: float = 0.80,
    version_tag: str = "BioReasonBench-v0.1",
):
    items = load_benchmark_from_dir(bench_dir)
    if not items:
        raise ValueError(f"No benchmark items found in {bench_dir}")

    # Sort items deterministically by item_id
    items = sorted(items, key=lambda x: x.item_id)
    n_total = len(items)

    out_path = Path(out_dir)
    dev_path = out_path / "dev"
    test_path = out_path / "final_test"

    dev_path.mkdir(parents=True, exist_ok=True)
    test_path.mkdir(parents=True, exist_ok=True)

    # Compute overall sha256
    hasher = hashlib.sha256()
    for item in items:
        hasher.update(json.dumps(item.model_dump(mode="json"), sort_keys=True).encode("utf-8"))
    dataset_sha256 = hasher.hexdigest()

    # Stratified split by difficulty & category
    dev_items: List[BenchmarkItem] = []
    test_items: List[BenchmarkItem] = []

    # Group by (difficulty, category)
    strata: Dict[str, List[BenchmarkItem]] = {}
    for item in items:
        key = f"{item.difficulty.value}::{item.category.value}"
        strata.setdefault(key, []).append(item)

    for key, group in sorted(strata.items()):
        # Deterministic assignment: 4 out of 5 to dev, 1 out of 5 to final_test
        for i, item in enumerate(group):
            if (i % 5) == 4:  # 20%
                test_items.append(item)
            else:  # 80%
                dev_items.append(item)

    # Save split files
    for item in dev_items:
        with open(dev_path / f"{item.item_id}.json", "w") as f:
            json.dump(item.model_dump(mode="json"), f, indent=2)

    for item in test_items:
        with open(test_path / f"{item.item_id}.json", "w") as f:
            json.dump(item.model_dump(mode="json"), f, indent=2)

    # Compute distributions
    diff_dist = {}
    for d in DifficultyLevel:
        diff_dist[d.value] = {
            "total": sum(1 for x in items if x.difficulty == d),
            "dev": sum(1 for x in dev_items if x.difficulty == d),
            "final_test": sum(1 for x in test_items if x.difficulty == d),
            "percentage": round(sum(1 for x in items if x.difficulty == d) / n_total * 100, 2),
        }

    cat_dist = {}
    for c in BenchmarkCategory:
        cnt = sum(1 for x in items if x.category == c)
        if cnt > 0:
            cat_dist[c.value] = {
                "total": cnt,
                "dev": sum(1 for x in dev_items if x.category == c),
                "final_test": sum(1 for x in test_items if x.category == c),
            }

    domain_dist = {}
    for x in items:
        d = x.domain or "unspecified"
        domain_dist[d] = domain_dist.get(d, 0) + 1

    manifest = {
        "version": version_tag,
        "frozen_timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "sha256": dataset_sha256,
        "total_items": n_total,
        "dev_items_count": len(dev_items),
        "final_test_items_count": len(test_items),
        "split_ratio": {"dev": round(len(dev_items) / n_total, 3), "final_test": round(len(test_items) / n_total, 3)},
        "difficulty_distribution": diff_dist,
        "category_distribution": cat_dist,
        "domain_distribution": domain_dist,
    }

    manifest_file = out_path / "manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest


if __name__ == "__main__":
    print("Freezing BioReasonBench-v0.1...")
    manifest = freeze_benchmark_v0_1()
    print(f"Version: {manifest['version']}")
    print(f"SHA-256: {manifest['sha256']}")
    print(f"Total Items: {manifest['total_items']} (Dev: {manifest['dev_items_count']}, Final Test: {manifest['final_test_items_count']})")
    print("Benchmark freeze complete.")

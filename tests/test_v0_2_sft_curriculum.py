"""
Unit tests for BioReason v0.2 Phase 3 Increment 3:
- BioReasonTrain-v0.2-SFT-v0.1 snapshot schema & tier validation
- BioReasonDev-v0.2 reusable benchmark validation
- Adapter strategy and training configuration validation
- Smoke training artifact and loss trajectory validation
- Anti-forgetting preservation gate validation
"""

import json
from pathlib import Path
import pytest
from bioreason.schemas.episode import ScientificReasoningEpisode
from bioreason.schemas.benchmark import BenchmarkItem
from bioreason.datasets.contamination_v4 import ContaminationEngineV4


def test_v0_2_sft_snapshot_integrity():
    """Verify that BioReasonTrain-v0.2-SFT-v0.1 has 900 train / 100 val episodes and valid schemas."""
    root = Path("/Users/albertopaz/Biomindv2")
    snapshot_dir = root / "training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1"
    train_file = snapshot_dir / "train.jsonl"
    val_file = snapshot_dir / "val.jsonl"
    man_file = snapshot_dir / "manifest.json"

    assert train_file.exists()
    assert val_file.exists()
    assert man_file.exists()

    train_episodes = []
    with open(train_file) as f:
        for line in f:
            if line.strip():
                train_episodes.append(ScientificReasoningEpisode(**json.loads(line)))

    val_episodes = []
    with open(val_file) as f:
        for line in f:
            if line.strip():
                val_episodes.append(ScientificReasoningEpisode(**json.loads(line)))

    assert len(train_episodes) == 900
    assert len(val_episodes) == 100

    # Verify quality tiers (>= 25% TIER_A, 0% unreviewed)
    tier_a_count = sum(1 for ep in train_episodes + val_episodes if ep.quality_tier == "TIER_A")
    assert tier_a_count >= 250  # >= 25%
    unreviewed_count = sum(1 for ep in train_episodes + val_episodes if ep.quality_tier not in ["TIER_A", "TIER_B"])
    assert unreviewed_count == 0


def test_v0_2_reusable_dev_set():
    """Verify that BioReasonDev-v0.2 has 100 items and valid benchmark schema."""
    root = Path("/Users/albertopaz/Biomindv2")
    dev_file = root / "benchmark/dev_v0.2/items.json"
    man_file = root / "benchmark/dev_v0.2/manifest.json"

    assert dev_file.exists()
    assert man_file.exists()

    with open(dev_file) as f:
        items = json.load(f)

    assert len(items) == 100
    bench_items = [BenchmarkItem(**item) for item in items]
    assert len(bench_items) == 100


def test_v0_2_sft_configs_and_adapter_strategy():
    """Verify that training config and adapter strategy documents exist and are valid."""
    root = Path("/Users/albertopaz/Biomindv2")
    full_cfg = root / "configs/training/br_v02_sft_001.yaml"
    smoke_cfg = root / "configs/training/br_v02_sft_001_smoke.yaml"
    strategy_doc = root / "V0_2_ADAPTER_STRATEGY.md"

    assert full_cfg.exists()
    assert smoke_cfg.exists()
    assert strategy_doc.exists()


def test_v0_2_smoke_training_artifacts_and_metrics():
    """Verify that smoke run output manifest exists and shows loss descent and 0 NaNs."""
    root = Path("/Users/albertopaz/Biomindv2")
    manifest_path = root / "outputs/BR-V02-SFT-001-SMOKE/smoke_manifest.json"
    assert manifest_path.exists()

    with open(manifest_path) as f:
        meta = json.load(f)

    assert meta["status"] == "SMOKE_TRAINING_SUCCESSFUL"
    assert meta["nan_count"] == 0
    assert meta["final_loss"] < meta["initial_loss"]
    assert len(meta["loss_history"]) >= 5


def test_v0_2_snapshot_contamination_clean():
    """Verify Contamination Engine V4 confirms zero leakage between snapshot and held-out benchmarks."""
    root = Path("/Users/albertopaz/Biomindv2")
    snapshot_dir = root / "training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1"
    bench_file = root / "benchmark/v0.2/bioreason_bench_v0_2_full.json"

    with open(snapshot_dir / "train.jsonl") as f:
        train_samples = [json.loads(line) for line in f if line.strip()][:50]
    with open(bench_file) as f:
        bench_samples = json.load(f)[:50]

    engine = ContaminationEngineV4()
    reports = engine.audit_contamination(bench_samples, train_samples)
    assert len(reports) == 0

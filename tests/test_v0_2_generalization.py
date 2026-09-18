"""
Unit tests for BioReason v0.2 Phase 3 Increment 2:
- Multi-hop ancestry leakage detection in ExperimentGraph
- BioReasonBench-v0.2 full dataset (100 items) integrity
- BioReasonChallenge-v0.1 full dataset (80 items) integrity
- BioReasonRegression-v0.1 dataset (100 items) integrity
- Peer Review and Study Design pilot schemas
- BioReasonTrain-v0.2 full candidate episodes (200 episodes) integrity and contamination firewall
"""

import json
from pathlib import Path
import pytest
from bioreason.schemas.experiment_graph import (
    ExperimentGraph,
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeRelation,
)
from bioreason.schemas.benchmark import BenchmarkItem
from bioreason.schemas.episode import ScientificReasoningEpisode
from bioreason.datasets.contamination_v4 import ContaminationEngineV4


def test_experiment_graph_multi_hop_ancestry_leakage():
    """Test multi-hop ancestry leakage detection when image tiles or sub-samples share a common patient ancestor."""
    g = ExperimentGraph(
        graph_id="GRAPH_MULTI_HOP_LEAK",
        name="Multi-Hop Image Tile Leakage",
        nodes=[
            GraphNode(node_id="patient_01", node_type=NodeType.PATIENT, label="Patient 1"),
            GraphNode(node_id="slide_01", node_type=NodeType.SAMPLE, label="Slide 1"),
            GraphNode(node_id="tile_01", node_type=NodeType.IMAGE_TILE, label="Tile 1"),
            GraphNode(node_id="tile_02", node_type=NodeType.IMAGE_TILE, label="Tile 2"),
            GraphNode(node_id="part_train", node_type=NodeType.PARTITION, label="Train Partition"),
            GraphNode(node_id="part_test", node_type=NodeType.PARTITION, label="Test Partition"),
        ],
        edges=[
            GraphEdge(source_id="slide_01", target_id="patient_01", relation=EdgeRelation.DERIVED_FROM),
            GraphEdge(source_id="tile_01", target_id="slide_01", relation=EdgeRelation.DERIVED_FROM),
            GraphEdge(source_id="tile_02", target_id="slide_01", relation=EdgeRelation.DERIVED_FROM),
            GraphEdge(source_id="tile_01", target_id="part_train", relation=EdgeRelation.ASSIGNED_TO),
            GraphEdge(source_id="tile_02", target_id="part_test", relation=EdgeRelation.ASSIGNED_TO),
        ]
    )

    issues = g.check_ancestry_partition_leakage()
    assert len(issues) >= 1
    assert "ANCESTRY_LEAKAGE" in issues[0]


def test_expanded_benchmark_v0_2_full():
    """Verify that BioReasonBench-v0.2 full dataset has 100 items, valid schema, and target distributions."""
    root = Path("/Users/albertopaz/Biomindv2")
    bench_file = root / "benchmark/v0.2/bioreason_bench_v0_2_full.json"
    assert bench_file.exists()

    with open(bench_file) as f:
        raw_items = json.load(f)

    assert len(raw_items) == 100
    items = [BenchmarkItem(**item) for item in raw_items]

    # Verify hard negatives in 20-30% range
    hard_negs = [i for i in items if not i.flawed_analysis_present]
    assert 20 <= len(hard_negs) <= 30

    # Verify domain diversity
    domains = {i.domain for i in items}
    assert len(domains) >= 10


def test_expanded_challenge_v0_1_full():
    """Verify that BioReasonChallenge-v0.1 full dataset has 80 items and valid presentation styles."""
    root = Path("/Users/albertopaz/Biomindv2")
    chall_file = root / "challenge/bioreason_challenge_v0.1/bioreason_challenge_v0_1_full.json"
    assert chall_file.exists()

    with open(chall_file) as f:
        items = json.load(f)

    assert len(items) == 80
    assert all("challenge_id" in item and "scenario" in item for item in items)


def test_regression_suite_v0_1():
    """Verify that BioReasonRegression-v0.1 has 100 reusable dev items and manifest."""
    root = Path("/Users/albertopaz/Biomindv2")
    regr_file = root / "benchmark/regression/bioreason_regression_v0_1.json"
    man_file = root / "benchmark/regression/manifest.json"

    assert regr_file.exists()
    assert man_file.exists()

    with open(regr_file) as f:
        items = json.load(f)
    assert len(items) == 100


def test_peer_review_and_study_design_pilots():
    """Verify that peer review and study design pilot protocols load correctly."""
    root = Path("/Users/albertopaz/Biomindv2")
    pr_file = root / "docs/pilots/peer_review_mode_pilot.json"
    sd_file = root / "docs/pilots/study_design_mode_pilot.json"
    schema_file = root / "docs/pilots/human_blind_evaluation_schema.json"

    assert pr_file.exists()
    assert sd_file.exists()
    assert schema_file.exists()

    with open(pr_file) as f:
        pr_items = json.load(f)
    with open(sd_file) as f:
        sd_items = json.load(f)

    assert len(pr_items) == 10
    assert len(sd_items) == 10


def test_expanded_candidate_training_episodes_v0_2():
    """Verify that candidate training dataset has 200 episodes and 0 contamination with benchmark."""
    root = Path("/Users/albertopaz/Biomindv2")
    train_file = root / "training_data/v0.2/candidate_episodes_v0_2_full.json"
    bench_file = root / "benchmark/v0.2/bioreason_bench_v0_2_full.json"

    with open(train_file) as f:
        raw_train = json.load(f)
    with open(bench_file) as f:
        raw_bench = json.load(f)

    assert len(raw_train) == 200
    train_episodes = [ScientificReasoningEpisode(**ep) for ep in raw_train]
    bench_items = [BenchmarkItem(**item) for item in raw_bench]

    engine = ContaminationEngineV4()
    reports = engine.audit_contamination(bench_items, train_episodes)
    assert len(reports) == 0

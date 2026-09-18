"""
Unit tests for BioReason v0.2 Foundation:
- ExperimentGraph topological representations and invariant checks
- Contamination Engine V4 multimodal firewall capabilities
- BioReasonBench v0.2, BioReasonChallenge v0.1, and BioReasonTrain v0.2 pilot dataset integrity
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
from bioreason.schemas.episode import ScientificReasoningEpisode, ScenarioSignature, SourceProvenance
from bioreason.datasets.contamination_v4 import ContaminationEngineV4, check_contamination_v4


def test_experiment_graph_topology_and_fingerprint():
    """Test ExperimentGraph construction and deterministic structural fingerprinting."""
    g = ExperimentGraph(
        graph_id="GRAPH_001_SPATIAL",
        name="Spatial Visium Study",
        nodes=[
            GraphNode(node_id="subj_01", node_type=NodeType.SUBJECT, label="Patient 1"),
            GraphNode(node_id="slice_01", node_type=NodeType.SAMPLE, label="Slice 1"),
            GraphNode(node_id="spot_01", node_type=NodeType.OBSERVATION, label="Spot 1"),
            GraphNode(node_id="part_train", node_type=NodeType.PARTITION, label="Train Partition"),
        ],
        edges=[
            GraphEdge(source_id="slice_01", target_id="subj_01", relation=EdgeRelation.DERIVED_FROM),
            GraphEdge(source_id="spot_01", target_id="slice_01", relation=EdgeRelation.DERIVED_FROM),
            GraphEdge(source_id="spot_01", target_id="part_train", relation=EdgeRelation.ASSIGNED_TO),
        ]
    )

    assert len(g.nodes) == 4
    assert len(g.edges) == 3
    fingerprint = g.compute_structural_fingerprint()
    assert isinstance(fingerprint, str)
    assert len(fingerprint) == 64  # sha256


def test_experiment_graph_leakage_detection():
    """Test topological partition leakage detection when a transformation processes both train and test partitions."""
    g = ExperimentGraph(
        graph_id="GRAPH_002_LEAKAGE",
        name="Global Scaling Leakage Graph",
        nodes=[
            GraphNode(node_id="part_train", node_type=NodeType.PARTITION, label="Train Partition"),
            GraphNode(node_id="part_test", node_type=NodeType.PARTITION, label="Test Partition"),
            GraphNode(node_id="trans_global_scaler", node_type=NodeType.TRANSFORMATION, label="Global StandardScaler"),
        ],
        edges=[
            GraphEdge(source_id="part_train", target_id="trans_global_scaler", relation=EdgeRelation.TRANSFORMED_BY),
            GraphEdge(source_id="part_test", target_id="trans_global_scaler", relation=EdgeRelation.TRANSFORMED_BY),
        ]
    )

    issues = g.check_partition_leakage()
    assert len(issues) == 1
    assert "LEAKAGE_DETECTED" in issues[0]


def test_experiment_graph_pseudoreplication_topology():
    """Test pseudoreplication detection when observations from one subject are split across train and test partitions."""
    g = ExperimentGraph(
        graph_id="GRAPH_003_PSEUDOREP",
        name="Subject Observation Split Across Partitions",
        nodes=[
            GraphNode(node_id="patient_01", node_type=NodeType.SUBJECT, label="Subject 1"),
            GraphNode(node_id="cell_01", node_type=NodeType.OBSERVATION, label="Cell 1"),
            GraphNode(node_id="cell_02", node_type=NodeType.OBSERVATION, label="Cell 2"),
            GraphNode(node_id="part_train", node_type=NodeType.PARTITION, label="Train Partition"),
            GraphNode(node_id="part_test", node_type=NodeType.PARTITION, label="Test Partition"),
        ],
        edges=[
            GraphEdge(source_id="cell_01", target_id="patient_01", relation=EdgeRelation.DERIVED_FROM),
            GraphEdge(source_id="cell_02", target_id="patient_01", relation=EdgeRelation.DERIVED_FROM),
            GraphEdge(source_id="cell_01", target_id="part_train", relation=EdgeRelation.ASSIGNED_TO),
            GraphEdge(source_id="cell_02", target_id="part_test", relation=EdgeRelation.ASSIGNED_TO),
        ]
    )

    issues = g.check_pseudoreplication_topology()
    assert len(issues) == 1
    assert "PSEUDOREPLICATION_LEAKAGE" in issues[0]


def test_contamination_v4_catches_all_levels():
    """Test that Contamination Engine V4 flags exact, normalized, signature, and provenance collisions."""
    engine = ContaminationEngineV4()

    # Exact Question
    cand_1 = {"item_id": "C1", "question": "What is the batch effect here?", "scenario": "Details"}
    ref_1 = {"item_id": "R1", "question": "What is the batch effect here?", "scenario": "Other details"}
    r1 = engine.audit_contamination([cand_1], [ref_1])
    assert any(x["contamination_type"] == "EXACT_QUESTION_MATCH" for x in r1)

    # Normalized Question
    cand_2 = {"item_id": "C2", "question": "What IS the batch effect, here?!?", "scenario": "Details"}
    ref_2 = {"item_id": "R2", "question": "what is the batch effect here", "scenario": "Details"}
    r2 = engine.audit_contamination([cand_2], [ref_2])
    assert any(x["contamination_type"] in ["EXACT_QUESTION_MATCH", "NORMALIZED_QUESTION_MATCH"] for x in r2)

    # Scenario Signature Collision
    cand_3 = {
        "item_id": "C3", "question": "Q1", "scenario": "Scen1",
        "scenario_signature": {"assay": "scrna_seq", "problem": "de", "experimental_unit": "animal", "analysis": "t_test", "failure_mode": "pseudoreplication"}
    }
    ref_3 = {
        "item_id": "R3", "question": "Q2 completely different text", "scenario": "Scen2",
        "scenario_signature": {"assay": "scrna_seq", "problem": "de", "experimental_unit": "animal", "analysis": "t_test", "failure_mode": "pseudoreplication"}
    }
    r3 = engine.audit_contamination([cand_3], [ref_3])
    assert any(x["contamination_type"] == "SCENARIO_SIGNATURE_COLLISION" for x in r3)

    # DOI / Source Provenance Overlap
    cand_4 = {"item_id": "C4", "question": "Q4", "scenario": "Scen4", "provenance": {"doi": "10.1038/s41592-021-01142-7"}}
    ref_4 = {"item_id": "R4", "question": "Q5", "scenario": "Scen5", "provenance": {"doi": "10.1038/s41592-021-01142-7"}}
    r4 = engine.audit_contamination([cand_4], [ref_4])
    assert any(x["contamination_type"] == "PROVENANCE_SOURCE_OVERLAP" for x in r4)


def test_v0_2_pilot_dataset_schema_validation():
    """Verify that all pilot datasets load cleanly and satisfy Pydantic validations."""
    root = Path("/Users/albertopaz/Biomindv2")

    bench_path = root / "benchmark/v0.2/bioreason_bench_v0_2_pilot.json"
    chall_path = root / "challenge/bioreason_challenge_v0.1/bioreason_challenge_v0_1.json"
    train_path = root / "training_data/v0.2/candidate_episodes_v0_2_pilot.json"

    assert bench_path.exists()
    assert chall_path.exists()
    assert train_path.exists()

    with open(bench_path) as f:
        bench_data = json.load(f)
    with open(chall_path) as f:
        chall_data = json.load(f)
    with open(train_path) as f:
        train_data = json.load(f)

    bench_items = [BenchmarkItem(**item) for item in bench_data]
    train_episodes = [ScientificReasoningEpisode(**ep) for ep in train_data]

    assert len(bench_items) == 25
    assert len(chall_data) == 25
    assert len(train_episodes) == 50

    # Verify hard negatives in benchmark
    hard_negatives = [b for b in bench_items if not b.flawed_analysis_present]
    assert len(hard_negatives) >= 5  # at least 20% hard negatives

    # Verify expert validation tiering
    expert_episodes = [ep for ep in train_episodes if ep.validation_status.value in ["expert_validated", "scientist_reviewed"]]
    assert len(expert_episodes) == 50  # 100% human/expert reviewed

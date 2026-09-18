"""
Unit tests for BioReason v0.2 Human External Validation Package and Locked Final Benchmark (Phase 3 Increment 7).
"""

import json
import hashlib
from pathlib import Path
import pytest


@pytest.fixture
def repo_root():
    return Path("/Users/albertopaz/Biomindv2")


def test_human_eval_package_integrity(repo_root):
    heval_dir = repo_root / "human_eval/v0.2"
    cases_file = heval_dir / "cases.jsonl"
    blinded_file = heval_dir / "blinded_responses.jsonl"
    schema_file = heval_dir / "review_schema.json"
    rand_manifest = heval_dir / "randomization_manifest.json"
    guide_file = heval_dir / "REVIEWER_GUIDE.md"

    assert cases_file.exists()
    assert blinded_file.exists()
    assert schema_file.exists()
    assert rand_manifest.exists()
    assert guide_file.exists()

    cases = [json.loads(line) for line in cases_file.read_text().splitlines() if line.strip()]
    blinded = [json.loads(line) for line in blinded_file.read_text().splitlines() if line.strip()]

    assert len(cases) == 50
    assert len(blinded) == 50

    with open(rand_manifest) as f:
        rand_data = json.load(f)

    assert rand_data["status"] == "SEALED_BLINDED_RANDOMIZATION_KEY"
    assert rand_data["total_cases"] == 50
    assert len(rand_data["randomization_mapping"]) == 50


def test_final_locked_benchmark_integrity(repo_root):
    final_dir = repo_root / "benchmark/final_v0.2"
    manifest_file = final_dir / "manifest.json"
    items_file = final_dir / "items.json"

    assert manifest_file.exists()
    assert items_file.exists()

    with open(manifest_file) as f:
        manifest = json.load(f)

    assert manifest["benchmark_name"] == "BioReasonBench-v0.2-Final"
    assert manifest["total_items"] == 120
    assert manifest["status"] == "SEALED_LOCKED_BENCHMARK"
    assert manifest["composition"]["valid_hard_negatives"] >= 30
    assert manifest["composition"]["insufficient_information_items"] >= 12

    items = json.loads(items_file.read_text())
    assert len(items) == 120

    calculated_sha = hashlib.sha256(items_file.read_bytes()).hexdigest()
    assert manifest["items_sha256"] == calculated_sha

    # Verify structured gold schema fields
    sample = items[0]
    assert "primary_assessment" in sample
    assert "experimental_unit" in sample
    assert "critical_issue" in sample
    assert "recommended_correction" in sample


def test_governance_and_strategy_documents(repo_root):
    baseline_doc = repo_root / "PHASE_3_INCREMENT_7_BASELINE.md"
    human_plan = repo_root / "HUMAN_EVALUATION_ANALYSIS_PLAN.md"
    final_plan = repo_root / "FINAL_V0_2_EVALUATION_PLAN.md"
    knowledge_strat = repo_root / "V0_2_KNOWLEDGE_EXPANSION_STRATEGY.md"
    model_card = repo_root / "MODEL_CARD_BIOREASON_V0_2_DRAFT.md"
    report_doc = repo_root / "PHASE_3_INCREMENT_7_REPORT.md"
    release_dir = repo_root / "releases/bioreason-v0.2-pre-final"

    assert baseline_doc.exists()
    assert human_plan.exists()
    assert final_plan.exists()
    assert knowledge_strat.exists()
    assert model_card.exists()
    assert report_doc.exists()
    assert (release_dir / "manifest.json").exists()
    assert (release_dir / "FINAL_V0_2_EVALUATION_PLAN.md").exists()

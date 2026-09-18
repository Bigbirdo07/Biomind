"""
Unit tests for Phase 3 Increment 8 Stage-A Human Review Gate & Final Benchmark Sealing.
"""

import json
import hashlib
from pathlib import Path
import pytest


@pytest.fixture
def repo_root():
    return Path("/Users/albertopaz/Biomindv2")


def test_baseline_and_review_status_documents(repo_root):
    baseline_doc = repo_root / "PHASE_3_INCREMENT_8_BASELINE.md"
    status_doc = repo_root / "HUMAN_REVIEW_STATUS.md"
    human_plan = repo_root / "HUMAN_EVALUATION_ANALYSIS_PLAN.md"
    final_plan = repo_root / "FINAL_V0_2_EVALUATION_PLAN.md"

    assert baseline_doc.exists()
    assert status_doc.exists()
    assert human_plan.exists()
    assert final_plan.exists()

    status_text = status_doc.read_text()
    assert "HUMAN_REVIEW_PENDING" in status_text
    assert "V0_2_HUMAN_REVIEW_PENDING" in status_text
    assert "SEALED" in status_text
    assert "UNTOUCHED" in status_text


def test_final_benchmark_is_sealed_and_unopened(repo_root):
    final_dir = repo_root / "benchmark/final_v0.2"
    manifest_file = final_dir / "manifest.json"
    items_file = final_dir / "items.json"

    assert manifest_file.exists()
    assert items_file.exists()

    with open(manifest_file) as f:
        manifest = json.load(f)

    expected_sha = "884dd9c5b677c13ae21b643046d3ef02d653a503e09bb8056fc34241bcbc35b2"
    assert manifest["items_sha256"] == expected_sha

    calculated_sha = hashlib.sha256(items_file.read_bytes()).hexdigest()
    assert calculated_sha == expected_sha
    assert manifest["status"] == "SEALED_LOCKED_BENCHMARK"


def test_human_eval_blinding_sealed(repo_root):
    rand_manifest = repo_root / "human_eval/v0.2/randomization_manifest.json"
    assert rand_manifest.exists()
    with open(rand_manifest) as f:
        rand_data = json.load(f)

    assert rand_data["status"] == "SEALED_BLINDED_RANDOMIZATION_KEY"
    assert rand_data["total_cases"] == 50

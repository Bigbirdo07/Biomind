"""
Tests for BioReason v0.2 Full SFT Experiment & Candidate Validation (Phase 3 Increment 4).
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def repo_root():
    return Path("/Users/albertopaz/Biomindv2")


def test_baseline_and_ablation_configs(repo_root):
    baseline_doc = repo_root / "PHASE_3_INCREMENT_4_BASELINE.md"
    assert baseline_doc.exists()

    config_a = repo_root / "configs/training/br_v02_sft_001.yaml"
    config_b = repo_root / "configs/training/br_v02_sft_001_b.yaml"
    assert config_a.exists()
    assert config_b.exists()


def test_sft_candidate_manifest_integrity(repo_root):
    manifest_path = repo_root / "BIOREASON_V0_2_SFT_CANDIDATE_MANIFEST.json"
    assert manifest_path.exists()
    with open(manifest_path) as f:
        manifest = json.load(f)

    assert manifest["candidate_name"] == "BioReason-v0.2-SFT-Candidate-001-A"
    assert manifest["status"] == "SELECTED_DEVELOPMENT_CANDIDATE"
    assert manifest["model_lineage"]["checkpoint_step"] == 112
    assert manifest["model_lineage"]["checkpoint_epoch"] == 2.0
    assert manifest["primary_development_results"]["overall_accuracy"] >= 0.90
    assert manifest["primary_development_results"]["scientific_false_alarm_rate"] == 0.0
    assert manifest["regression_suite_results"]["overall_accuracy"] >= 0.95
    assert manifest["regression_suite_results"]["scientific_false_alarm_rate"] == 0.0


def test_full_evaluation_results_and_reports(repo_root):
    eval_path = repo_root / "outputs/BR-V02-SFT-001-A/full_evaluation_results.json"
    assert eval_path.exists()
    with open(eval_path) as f:
        results = json.load(f)

    assert results["bench_v02_metrics"]["v02_accuracy"] >= 0.90
    assert results["bench_v02_metrics"]["v02_false_alarm_rate"] == 0.0
    assert results["challenge_v01_metrics"]["v02_accuracy"] >= 0.85
    assert results["transition_analysis"]["NET_SCIENTIFIC_GAIN"] > 0
    assert len(results["domain_breakdown"]) >= 10
    assert len(results["style_breakdown"]) == 6

    report_path = repo_root / "PHASE_3_INCREMENT_4_FULL_SFT_REPORT.md"
    error_review = repo_root / "V0_2_SFT_ERROR_REVIEW.md"
    assert report_path.exists()
    assert error_review.exists()

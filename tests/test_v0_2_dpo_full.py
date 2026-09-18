"""
Unit tests for BioReason v0.2 Full DPO & Pre-Final Candidate Freeze (Phase 3 Increment 6).
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def repo_root():
    return Path("/Users/albertopaz/Biomindv2")


def test_preference_v0_2_dataset_integrity(repo_root):
    pref_dir = repo_root / "training_data/preferences/BioReasonPreference-v0.2-DPO-v0.2"
    manifest_file = pref_dir / "manifest.json"
    train_file = pref_dir / "train.jsonl"
    val_file = pref_dir / "val.jsonl"

    assert manifest_file.exists()
    assert train_file.exists()
    assert val_file.exists()

    with open(manifest_file) as f:
        manifest = json.load(f)

    assert manifest["total_pairs"] == 250
    assert manifest["train_pairs"] == 215
    assert manifest["val_pairs"] == 35
    assert manifest["valid_hard_negative_pct"] >= 20.0
    assert manifest["review_distribution"]["Unreviewed"] == 0

    train_lines = [line for line in train_file.read_text().splitlines() if line.strip()]
    val_lines = [line for line in val_file.read_text().splitlines() if line.strip()]
    assert len(train_lines) == 215
    assert len(val_lines) == 35


def test_pre_final_candidate_manifest(repo_root):
    manifest_file = repo_root / "BIOREASON_V0_2_PRE_FINAL_CANDIDATE_MANIFEST.json"
    assert manifest_file.exists()
    with open(manifest_file) as f:
        manifest = json.load(f)

    assert manifest["candidate_name"] == "BioReason-v0.2-Pre-Final-Candidate-001"
    assert manifest["status"] == "FROZEN_PRE_FINAL_CANDIDATE"
    assert manifest["verdicts"]["model_selection_verdict"] == "DPO_RETAINED"
    assert manifest["development_performance"]["overall_accuracy"] >= 0.95
    assert manifest["development_performance"]["scientific_false_alarm_rate"] == 0.0
    assert manifest["regression_suite_preservation"]["overall_accuracy"] >= 0.95
    assert manifest["regression_suite_preservation"]["scientific_false_alarm_rate"] == 0.0
    assert manifest["external_diagnostic_performance"]["bioreason_bench_v0_2"]["overall_accuracy"] >= 0.94
    assert manifest["external_diagnostic_performance"]["bioreason_challenge_v0_1"]["overall_accuracy"] >= 0.88


def test_dpo_reports_and_configs(repo_root):
    config_a = repo_root / "configs/training/br_v02_dpo_001_a.yaml"
    config_b = repo_root / "configs/training/br_v02_dpo_001_b.yaml"
    baseline_doc = repo_root / "PHASE_3_INCREMENT_6_BASELINE.md"
    dpo_report = repo_root / "PHASE_3_INCREMENT_6_FULL_DPO_REPORT.md"
    error_review = repo_root / "V0_2_DPO_ERROR_REVIEW.md"
    knowledge_backlog = repo_root / "V0_2_KNOWLEDGE_GAP_BACKLOG.md"

    assert config_a.exists()
    assert config_b.exists()
    assert baseline_doc.exists()
    assert dpo_report.exists()
    assert error_review.exists()
    assert knowledge_backlog.exists()

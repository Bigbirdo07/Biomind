"""
Unit tests for BioReason v0.2 DPO Smoke & Residual Error Audit (Phase 3 Increment 5).
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def repo_root():
    return Path("/Users/albertopaz/Biomindv2")


def test_baseline_and_audit_documents(repo_root):
    baseline = repo_root / "PHASE_3_INCREMENT_5_BASELINE.md"
    error_audit = repo_root / "V0_2_SFT_RESIDUAL_ERROR_AUDIT.md"
    pref_readiness = repo_root / "V0_2_PREFERENCE_READINESS_AUDIT.md"
    knowledge_backlog = repo_root / "V0_2_KNOWLEDGE_GAP_BACKLOG.md"
    smoke_report = repo_root / "PHASE_3_INCREMENT_5_DPO_SMOKE_REPORT.md"

    assert baseline.exists()
    assert error_audit.exists()
    assert pref_readiness.exists()
    assert knowledge_backlog.exists()
    assert smoke_report.exists()


def test_preference_dataset_manifest_and_pairs(repo_root):
    pref_dir = repo_root / "training_data/preferences/BioReasonPreference-v0.2-DPO-v0.1"
    manifest_file = pref_dir / "manifest.json"
    train_file = pref_dir / "train.jsonl"
    val_file = pref_dir / "val.jsonl"

    assert manifest_file.exists()
    assert train_file.exists()
    assert val_file.exists()

    with open(manifest_file) as f:
        manifest = json.load(f)

    assert manifest["total_pairs"] == 80
    assert manifest["train_pairs"] == 60
    assert manifest["val_pairs"] == 20
    assert manifest["valid_hard_negative_pct"] >= 20.0
    assert manifest["review_status_distribution"]["Unreviewed"] == 0

    train_lines = [line for line in train_file.read_text().splitlines() if line.strip()]
    val_lines = [line for line in val_file.read_text().splitlines() if line.strip()]
    assert len(train_lines) == 60
    assert len(val_lines) == 20

    sample = json.loads(train_lines[0])
    assert "preference_id" in sample
    assert "prompt" in sample
    assert "preferred_response" in sample
    assert "rejected_response" in sample
    assert "preference_reason" in sample


def test_dpo_smoke_outputs(repo_root):
    out_dir = repo_root / "outputs/BR-V02-DPO-001-SMOKE"
    manifest_file = out_dir / "smoke_manifest.json"
    eval_file = out_dir / "smoke_evaluation_results.json"

    assert manifest_file.exists()
    assert eval_file.exists()

    with open(eval_file) as f:
        eval_data = json.load(f)

    assert eval_data["dev_v02_metrics"]["accuracy"] >= 0.94
    assert eval_data["dev_v02_metrics"]["false_alarm_rate"] == 0.0
    assert eval_data["regression_v01_metrics"]["accuracy"] >= 0.95
    assert eval_data["transition_analysis"]["NET_SCIENTIFIC_GAIN"] > 0
    assert eval_data["dpo_smoke_verdict"] == "V0_2_DPO_SMOKE_BENEFICIAL"
    assert eval_data["full_dpo_readiness_verdict"] == "V0_2_FULL_DPO_READY"

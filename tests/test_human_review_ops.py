"""
tests/test_human_review_ops.py

Comprehensive tests for BioReason v0.2 External Human Review Operations &
Scorecard Ingestion Infrastructure (Phase 3 Increment 8B).

Governance Invariants Verified:
1. Zero human score fabrication.
2. Complete double-blinding preservation across packets & assignments.
3. Strict schema validation and duplicate rejection.
4. Dataset freeze safety gates.
5. Protection of locked final benchmark (BioReasonBench-v0.2-Final).
"""

import sys
import os
import json
import hashlib
import tempfile
import shutil
from pathlib import Path
import pytest

# Ensure scripts directory is in path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from validate_human_review_submission import (
    validate_single_record,
    validate_file,
    parse_csv_submission
)
from ingest_human_reviews import ingest_records, update_review_status, load_existing_submissions
from freeze_human_review_dataset import verify_completeness_and_validity, freeze_reviews
from analyze_human_evaluation import analyze_dataset, compute_trust_score, compute_krippendorff_alpha_ordinal


def test_assignment_generation_and_coverage():
    manifest_path = Path("human_eval/v0.2/assignments/reviewer_assignment_manifest.json")
    assert manifest_path.exists(), "Assignment manifest must exist."

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["total_cases"] == 50
    assert manifest["reviews_per_case_distribution"]["less_than_2"] == 0, "All cases must have >= 2 reviews."
    assert manifest["reviews_per_case_distribution"]["3_reviews"] >= 15, "At least 15 priority cases must receive triple review."

    # Verify no reviewer sees duplicate cases
    reviewers = manifest.get("reviewers", [])
    case_assignments = manifest.get("case_assignments", {})

    reviewer_cases = {r["reviewer_id"]: [] for r in reviewers}
    for cid, revs in case_assignments.items():
        assert len(revs) >= 2, f"Case {cid} has fewer than 2 assigned reviewers."
        assert len(revs) == len(set(revs)), f"Duplicate reviewer assigned to case {cid}"
        for r in revs:
            reviewer_cases[r].append(cid)

    # Workload balance check (each reviewer between 10 and 20 cases)
    for r_id, cases in reviewer_cases.items():
        assert 10 <= len(cases) <= 20, f"Reviewer {r_id} has unbalanced workload: {len(cases)} cases"


def test_reviewer_packet_structure_and_blinding():
    packets_dir = Path("human_eval/v0.2/reviewer_packets")
    assert packets_dir.exists(), "Packets directory must exist."

    expected_reviewers = [f"REV00{i}" for i in range(1, 9)]
    for r_id in expected_reviewers:
        r_dir = packets_dir / r_id
        assert r_dir.exists(), f"Packet for {r_id} missing."
        assert (r_dir / "assigned_cases.json").exists()
        assert (r_dir / "scorecard_template.csv").exists()
        assert (r_dir / "viewer.html").exists()
        assert (r_dir / "REVIEWER_GUIDE.md").exists()

        # Check that randomization manifest is NOT in the packet
        assert not (r_dir / "randomization_manifest.json").exists()

        # Check assigned_cases.json for model identity leaks
        with open(r_dir / "assigned_cases.json", "r", encoding="utf-8") as f:
            content = f.read().lower()
            assert "qwen" not in content, f"Model leakage in {r_id} assigned_cases.json"
            assert "br-dpo" not in content
            assert "br-sft" not in content
            assert "checkpoint-step" not in content


def test_submission_schema_validation():
    fixtures_dir = Path("tests/fixtures/human_eval_synthetic")

    # 1. Valid fixture passes
    valid_file = fixtures_dir / "valid_submission.json"
    ok, count, errs = validate_file(valid_file)
    assert ok is True, f"Valid submission failed: {errs}"
    assert count == 1

    # 2. Out-of-bounds score fails
    inv_score_file = fixtures_dir / "invalid_score_submission.json"
    ok, count, errs = validate_file(inv_score_file)
    assert ok is False
    assert any("has invalid score '6'" in e for e in errs)

    # 3. Invalid enum fails
    inv_enum_file = fixtures_dir / "invalid_enum_submission.json"
    ok, count, errs = validate_file(inv_enum_file)
    assert ok is False
    assert any("qualification_tier" in e for e in errs)
    assert any("reviewer_confidence" in e for e in errs)
    assert any("pairwise_preference" in e for e in errs)

    # 4. Leaking model name in comments fails
    leak_file = fixtures_dir / "leaking_model_name_submission.json"
    ok, count, errs = validate_file(leak_file)
    assert ok is False
    assert any("forbidden model-revealing token" in e for e in errs)


def test_ingestion_and_duplicate_prevention(tmp_path):
    fixtures_dir = Path("tests/fixtures/human_eval_synthetic")
    with open(fixtures_dir / "valid_submission.json", "r", encoding="utf-8") as f:
        records = json.load(f)

    manifest_assignments = {"REV001": ["HEVAL_001"]}
    submissions_dir = tmp_path / "submissions"
    status_file = tmp_path / "review_status.json"

    # Ingest record 1st time -> OK
    ingested, rejected, errors = ingest_records(
        records, submissions_dir, manifest_assignments, allow_correction=False
    )
    assert ingested == 1
    assert rejected == 0

    # Ingest exact duplicate -> Rejected
    ingested2, rejected2, errors2 = ingest_records(
        records, submissions_dir, manifest_assignments, allow_correction=False
    )
    assert ingested2 == 0
    assert rejected2 == 1
    assert "Duplicate submission rejected" in errors2[0]

    # Ingest with versioned correction -> Allowed
    ingested3, rejected3, errors3 = ingest_records(
        records, submissions_dir, manifest_assignments,
        allow_correction=True, correction_reason="Reviewer updated rating"
    )
    assert ingested3 == 1
    assert rejected3 == 0
    assert (submissions_dir / "audit_corrections.json").exists()


def test_freeze_safety_gate_rejects_incomplete(tmp_path):
    manifest_path = Path("human_eval/v0.2/assignments/reviewer_assignment_manifest.json")
    cases_path = Path("human_eval/v0.2/cases.jsonl")
    empty_submissions_dir = tmp_path / "empty_submissions"
    empty_submissions_dir.mkdir()
    frozen_dir = tmp_path / "frozen"

    ok, errors, _ = verify_completeness_and_validity(empty_submissions_dir, manifest_path, cases_path)
    assert ok is False
    assert "No human review submissions found" in errors[0]

    # Freeze should fail
    freeze_ok, status_str = freeze_reviews(empty_submissions_dir, frozen_dir, manifest_path, cases_path)
    assert freeze_ok is False
    assert status_str == "FREEZE_FAILED_INCOMPLETE_OR_INVALID"


def test_full_freeze_and_analysis_on_synthetic_fixture(tmp_path):
    """
    Validates complete pipeline: generate full synthetic review coverage,
    freeze dataset, and run pre-registered analysis.
    """
    manifest_path = Path("human_eval/v0.2/assignments/reviewer_assignment_manifest.json")
    cases_path = Path("human_eval/v0.2/cases.jsonl")
    unblinding_key_path = Path("human_eval/v0.2/randomization_manifest.json")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Build complete synthetic submissions covering all assignments
    synthetic_submissions_dir = tmp_path / "synthetic_submissions"
    synthetic_submissions_dir.mkdir()

    dimensions = [
        "SCIENTIFIC_CORRECTNESS",
        "PRIMARY_ISSUE_IDENTIFICATION",
        "EXPERIMENTAL_UNIT_REASONING",
        "STATISTICAL_VALIDITY",
        "BIOLOGICAL_PLAUSIBILITY",
        "CORRECTION_ACTIONABILITY",
        "UNCERTAINTY_CALIBRATION",
        "OVERCLAIMING",
        "FALSE_ALARM_BEHAVIOR",
        "OVERALL_SCIENTIFIC_USEFULNESS"
    ]

    for cid, rev_list in manifest["case_assignments"].items():
        for r_id in rev_list:
            eval_a = {dim: 4 for dim in dimensions}
            eval_b = {dim: 2 for dim in dimensions}
            eval_c = {dim: 3 for dim in dimensions}
            record = {
                "_fixture_type": "SYNTHETIC_TEST_FIXTURE",
                "schema_version": "v0.2",
                "reviewer_id": r_id,
                "case_id": cid,
                "qualification_tier": "BIOSTATISTICIAN",
                "reviewer_confidence": "HIGH",
                "response_evaluations": {
                    "RESPONSE_A": eval_a,
                    "RESPONSE_B": eval_b,
                    "RESPONSE_C": eval_c
                },
                "pairwise_preference": "RESPONSE_A",
                "comments": "Synthetic test comment.",
                "submitted_at": "2026-09-16T00:00:00Z"
            }
            with open(synthetic_submissions_dir / f"{r_id}_{cid}.json", "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2)

    # Test Freeze on synthetic complete dataset
    frozen_dir = tmp_path / "frozen_reviews"
    freeze_ok, manifest_sha = freeze_reviews(synthetic_submissions_dir, frozen_dir, manifest_path, cases_path)
    assert freeze_ok is True
    assert (frozen_dir / "review_manifest.json").exists()

    # Test Analysis execution on synthetic frozen dataset
    analysis_results = analyze_dataset(frozen_dir, unblinding_key_path)
    assert analysis_results["total_reviews_analyzed"] == manifest["total_case_reviews_planned"]
    assert "model_performance" in analysis_results
    assert "pairwise_preferences" in analysis_results
    assert "inter_rater_reliability" in analysis_results
    assert "scientist_trust_score_exploratory" in analysis_results["model_performance"]["v0.2"]


def test_governance_final_benchmark_protection():
    """Verify that operational scripts do NOT access or reference benchmark/final_v0.2/items.json."""
    scripts_to_check = [
        "generate_human_review_assignments.py",
        "validate_human_review_submission.py",
        "ingest_human_reviews.py",
        "freeze_human_review_dataset.py",
        "analyze_human_evaluation.py"
    ]

    for s in scripts_to_check:
        s_path = SCRIPTS_DIR / s
        assert s_path.exists(), f"Script {s} missing."
        content = s_path.read_text(encoding="utf-8")
        assert "benchmark/final_v0.2/items.json" not in content, f"Script {s} references sealed final benchmark!"

    # Verify locked final benchmark SHA-256
    items_path = Path("benchmark/final_v0.2/items.json")
    assert items_path.exists()
    h = hashlib.sha256(items_path.read_bytes()).hexdigest()
    assert h == "884dd9c5b677c13ae21b643046d3ef02d653a503e09bb8056fc34241bcbc35b2"


def test_current_human_review_verdict():
    """Verify that no fabricated reviews exist in the official human_eval directory."""
    submissions_dir = Path("human_eval/v0.2/submissions")
    data_files = [f for f in submissions_dir.glob("*.json") if f.name != "review_status.json" and not f.name.startswith("audit_")]
    assert len(data_files) == 0, "No real human reviews must be present yet."

    status_path = Path("human_eval/v0.2/review_status.json")
    assert status_path.exists()
    with open(status_path, "r", encoding="utf-8") as f:
        st = json.load(f)

    assert st["status"] == "PACKAGE_READY"
    assert st["completed_reviews"] == 0
    assert st["remaining_reviews"] == 117

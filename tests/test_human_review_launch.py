"""
tests/test_human_review_launch.py

Tests for BioReason v0.2 Reviewer Recruitment, Packet Distribution, and
Human Evaluation Launch (Phase 3 Increment 8C).

Governance Invariants:
1. Packet hash integrity and manifest conformance.
2. Reviewer registry and distribution log structure.
3. Privacy controls on sensitive operational data.
4. Reassignment auditability.
5. Final benchmark logical sealing.
"""

import sys
import os
import json
import csv
import hashlib
import tempfile
import shutil
from pathlib import Path
import pytest

# Ensure scripts directory is in path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_packet_manifest import build_manifest, compute_file_sha256
from reassign_human_reviewer import reassign_reviewer


def test_packet_manifest_integrity():
    manifest_path = Path("human_eval/v0.2/reviewer_packets/PACKET_MANIFEST.json")
    assert manifest_path.exists(), "PACKET_MANIFEST.json must exist."

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["manifest_version"] == "v0.2.0"
    assert manifest["total_packets"] == 8

    packets_dir = Path("human_eval/v0.2/reviewer_packets")
    for r_id, pdata in manifest["packets"].items():
        assert pdata["reviewer_id"] == r_id
        assert 10 <= pdata["case_count"] <= 20
        assert len(pdata["case_ids"]) == pdata["case_count"]

        # Verify actual file hashes on disk match manifest
        p_dir = packets_dir / r_id
        for fname, expected_hash in pdata["file_hashes"].items():
            fpath = p_dir / fname
            assert fpath.exists()
            actual_hash = compute_file_sha256(fpath)
            assert actual_hash == expected_hash, f"Hash mismatch for {r_id}/{fname}"


def test_reviewer_registry_template():
    registry_path = Path("human_eval/v0.2/reviewer_registry.template.csv")
    assert registry_path.exists(), "reviewer_registry.template.csv must exist."

    valid_statuses = {
        "INVITED", "ACCEPTED", "PACKET_ASSIGNED", "IN_PROGRESS",
        "SUBMITTED", "VALIDATED", "DECLINED", "WITHDRAWN"
    }

    with open(registry_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 8
    for row in rows:
        assert row["reviewer_id"].startswith("REV")
        assert row["status"] in valid_statuses
        assert row["prior_bioreason_involvement"] in {"NONE", "INFORMAL_FEEDBACK", "CONTRIBUTOR"}
        assert row["acknowledgment_preference"] in {"NAMED", "ANONYMOUS", "NONE"}


def test_distribution_log_template():
    log_path = Path("human_eval/v0.2/REVIEW_DISTRIBUTION_LOG.template.csv")
    assert log_path.exists(), "REVIEW_DISTRIBUTION_LOG.template.csv must exist."

    with open(log_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 8
    for row in rows:
        assert row["reviewer_id"].startswith("REV")
        assert row["packet_version"] == "v0.2.0"


def test_privacy_directory_gitignore():
    privacy_dir = Path("human_eval/v0.2/private_operations")
    assert privacy_dir.exists(), "private_operations directory must exist."
    gitignore_file = privacy_dir / ".gitignore"
    assert gitignore_file.exists(), ".gitignore must exist in private_operations."
    content = gitignore_file.read_text(encoding="utf-8")
    assert "*" in content


def test_reviewer_demo_example():
    demo_path = Path("human_eval/v0.2/reviewer_packets/DEMO_EXAMPLE.json")
    assert demo_path.exists(), "DEMO_EXAMPLE.json must exist."

    with open(demo_path, "r", encoding="utf-8") as f:
        demo = json.load(f)

    assert "DEMONSTRATION_ONLY" in demo.get("_notice", "")
    assert demo["demo_case_id"] == "DEMO_SCENARIO_001"
    assert "sample_blinded_responses" in demo
    assert "sample_expert_evaluation" in demo
    eval_data = demo["sample_expert_evaluation"]
    assert eval_data["pairwise_preference"] == "RESPONSE_A"
    assert eval_data["reviewer_confidence"] == "HIGH"


def test_launch_checklist_verified():
    checklist_path = Path("human_eval/v0.2/HUMAN_REVIEW_LAUNCH_CHECKLIST.md")
    assert checklist_path.exists(), "Launch checklist must exist."
    content = checklist_path.read_text(encoding="utf-8")
    assert "HUMAN_EVALUATION_LAUNCH_READY" in content
    assert "PASS" in content


def test_reassignment_tooling(tmp_path):
    # Setup mock environment in tmp_path
    assignments_dir = tmp_path / "assignments"
    packets_dir = tmp_path / "packets"
    assignments_dir.mkdir()
    packets_dir.mkdir()

    # Copy actual manifest & cases
    shutil.copy("human_eval/v0.2/assignments/reviewer_assignment_manifest.json", assignments_dir)
    cases_path = Path("human_eval/v0.2/cases.jsonl")
    responses_path = Path("human_eval/v0.2/blinded_responses.jsonl")
    guide_path = Path("human_eval/v0.2/REVIEWER_GUIDE.md")

    # Initial packets build in tmp
    manifest_src = json.loads(Path("human_eval/v0.2/assignments/reviewer_assignment_manifest.json").read_text())
    from generate_human_review_assignments import load_cases_and_responses, create_reviewer_packet
    cases_dict = load_cases_and_responses(str(cases_path), str(responses_path))

    for r in manifest_src["reviewers"]:
        r_id = r["reviewer_id"]
        c_ids = [cid for cid, revs in manifest_src["case_assignments"].items() if r_id in revs]
        create_reviewer_packet(r, c_ids, cases_dict, packets_dir, guide_path)

    # Execute reassignment: replace REV001 with REV009
    ok = reassign_reviewer(
        "REV001", "REV009", "BIOSTATISTICIAN",
        "REV001 declared scheduling conflict",
        assignments_dir, packets_dir, cases_path, responses_path, guide_path
    )
    assert ok is True

    # Verify updated manifest
    with open(assignments_dir / "reviewer_assignment_manifest.json", "r") as f:
        updated_man = json.load(f)

    assert "REV001" not in [r["reviewer_id"] for r in updated_man["reviewers"]]
    assert "REV009" in [r["reviewer_id"] for r in updated_man["reviewers"]]
    assert (assignments_dir / "audit_reassignments.json").exists()
    assert (packets_dir / "REV009" / "viewer.html").exists()


def test_governance_benchmark_sealing():
    items_path = Path("benchmark/final_v0.2/items.json")
    assert items_path.exists()
    h = hashlib.sha256(items_path.read_bytes()).hexdigest()
    assert h == "884dd9c5b677c13ae21b643046d3ef02d653a503e09bb8056fc34241bcbc35b2"

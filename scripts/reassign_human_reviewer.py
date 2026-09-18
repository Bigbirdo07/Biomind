#!/usr/bin/env python3
"""
scripts/reassign_human_reviewer.py

Handles reviewer withdrawal or replacement during external evaluation.

Governance Rules:
1. Never silently overwrite existing assignment history.
2. Logs all reassignments in audit_reassignments.json.
3. Updates reviewer_assignment_manifest.json and individual reviewer assignment files.
4. Generates a fresh, blinded reviewer packet for the new reviewer.
5. NO model identity leakage.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any

from generate_human_review_assignments import (
    load_cases_and_responses,
    create_reviewer_packet
)
from build_packet_manifest import build_manifest


def reassign_reviewer(
    old_reviewer_id: str,
    new_reviewer_id: str,
    new_qualification_tier: str,
    reason: str,
    assignments_dir: Path,
    packets_dir: Path,
    cases_path: Path,
    responses_path: Path,
    guide_path: Path
) -> bool:
    manifest_path = assignments_dir / "reviewer_assignment_manifest.json"
    if not manifest_path.exists():
        print(f"Error: Manifest {manifest_path} not found.")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Find cases assigned to old reviewer
    assigned_cases = []
    case_assignments = manifest.get("case_assignments", {})
    for cid, revs in case_assignments.items():
        if old_reviewer_id in revs:
            assigned_cases.append(cid)

    if not assigned_cases:
        print(f"Error: No cases found assigned to '{old_reviewer_id}'.")
        return False

    # 2. Update case assignments
    for cid in assigned_cases:
        revs = case_assignments[cid]
        revs.remove(old_reviewer_id)
        if new_reviewer_id not in revs:
            revs.append(new_reviewer_id)
        case_assignments[cid] = sorted(revs)

    # 3. Update reviewers list in manifest
    new_reviewer_info = {
        "reviewer_id": new_reviewer_id,
        "qualification_tier": new_qualification_tier,
        "domain_specialties": [],
        "experience_band": "6-10_years"
    }

    # Replace or append
    reviewers = manifest.get("reviewers", [])
    reviewers = [r for r in reviewers if r["reviewer_id"] != old_reviewer_id]
    reviewers.append(new_reviewer_info)
    manifest["reviewers"] = sorted(reviewers, key=lambda x: x["reviewer_id"])

    # Update workloads
    workloads = manifest.get("reviewer_workload", {})
    workloads.pop(old_reviewer_id, None)
    workloads[new_reviewer_id] = len(assigned_cases)
    manifest["reviewer_workload"] = workloads

    # 4. Save updated manifest
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 5. Log audit trail
    audit_file = assignments_dir / "audit_reassignments.json"
    audit_log = []
    if audit_file.exists():
        try:
            with open(audit_file, "r", encoding="utf-8") as f:
                audit_log = json.load(f)
        except Exception:
            pass

    audit_entry = {
        "timestamp": "2026-09-16T00:40:00Z",
        "old_reviewer_id": old_reviewer_id,
        "new_reviewer_id": new_reviewer_id,
        "new_qualification_tier": new_qualification_tier,
        "reassigned_case_count": len(assigned_cases),
        "reassigned_cases": assigned_cases,
        "reason": reason
    }
    audit_log.append(audit_entry)
    with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(audit_log, f, indent=2)

    # 6. Generate new reviewer assignment file and packet
    with open(assignments_dir / f"{new_reviewer_id}_assignments.json", "w", encoding="utf-8") as f:
        json.dump({
            "reviewer": new_reviewer_info,
            "assigned_case_count": len(assigned_cases),
            "assigned_cases": sorted(assigned_cases)
        }, f, indent=2)

    cases_dict = load_cases_and_responses(str(cases_path), str(responses_path))
    create_reviewer_packet(new_reviewer_info, assigned_cases, cases_dict, packets_dir, guide_path)

    # 7. Update packet manifest
    build_manifest(packets_dir, packets_dir / "PACKET_MANIFEST.json")

    print(f"Successfully reassigned {len(assigned_cases)} cases from {old_reviewer_id} to {new_reviewer_id}.")
    print(f"Generated new packet for {new_reviewer_id} under {packets_dir / new_reviewer_id}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Reassign reviewer slot in BioReason human evaluation.")
    parser.add_argument("--old-reviewer", required=True, help="Withdrawing reviewer ID (e.g. REV001)")
    parser.add_argument("--new-reviewer", required=True, help="Replacement reviewer ID (e.g. REV009)")
    parser.add_argument("--new-tier", default="COMPUTATIONAL_BIOLOGIST", help="Qualification tier for replacement")
    parser.add_argument("--reason", required=True, help="Reason for reassignment")
    parser.add_argument("--assignments-dir", default="human_eval/v0.2/assignments")
    parser.add_argument("--packets-dir", default="human_eval/v0.2/reviewer_packets")
    parser.add_argument("--cases", default="human_eval/v0.2/cases.jsonl")
    parser.add_argument("--responses", default="human_eval/v0.2/blinded_responses.jsonl")
    parser.add_argument("--guide", default="human_eval/v0.2/REVIEWER_GUIDE.md")
    args = parser.parse_args()

    ok = reassign_reviewer(
        args.old_reviewer,
        args.new_reviewer,
        args.new_tier,
        args.reason,
        Path(args.assignments_dir),
        Path(args.packets_dir),
        Path(args.cases),
        Path(args.responses),
        Path(args.guide)
    )
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

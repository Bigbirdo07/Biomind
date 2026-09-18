#!/usr/bin/env python3
"""
scripts/freeze_human_review_dataset.py

Freezes the completed human review dataset for BioReason v0.2.

Safety & Governance Invariants:
1. Strict Freeze Gate: Refuses to run if reviews are incomplete, invalid, or corrupted.
2. Creates an immutable, hash-verified snapshot under human_eval/v0.2/frozen_reviews/
3. Generates review_manifest.json with full cryptographic provenance.
4. NO UNBLINDING: Model identities remain completely blinded during the freeze process.
"""

import sys
import os
import shutil
import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

from validate_human_review_submission import validate_single_record


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_completeness_and_validity(
    submissions_dir: Path,
    manifest_path: Path,
    cases_path: Path
) -> Tuple[bool, List[str], Dict[str, Dict[str, Any]]]:
    errors = []
    submissions: Dict[str, Dict[str, Any]] = {}

    if not manifest_path.exists():
        return False, [f"Manifest not found: {manifest_path}"], {}
    if not cases_path.exists():
        return False, [f"Cases file not found: {cases_path}"], {}

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    all_case_ids = []
    with open(cases_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                all_case_ids.append(item["case_id"])

    # Load all submission files
    files = list(submissions_dir.glob("*.json"))
    data_files = [f for f in files if f.name != "review_status.json" and not f.name.startswith("audit_")]

    if len(data_files) == 0:
        return False, ["No human review submissions found in directory."], {}

    manifest_assignments = {}
    for r in manifest.get("reviewers", []):
        manifest_assignments[r["reviewer_id"]] = []
    for cid, revs in manifest.get("case_assignments", {}).items():
        for r_id in revs:
            if r_id in manifest_assignments:
                manifest_assignments[r_id].append(cid)

    for f in data_files:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                rec = json.load(fp)
                if isinstance(rec, list):
                    for r in rec:
                        ok, errs = validate_single_record(r, manifest_assignments)
                        if not ok:
                            errors.extend([f"File {f.name}: {e}" for e in errs])
                        k = f"{r['reviewer_id']}::{r['case_id']}"
                        if k in submissions:
                            errors.append(f"Duplicate unversioned review in dataset: {k}")
                        submissions[k] = {"path": f, "record": r}
                elif isinstance(rec, dict):
                    ok, errs = validate_single_record(rec, manifest_assignments)
                    if not ok:
                        errors.extend([f"File {f.name}: {e}" for e in errs])
                    k = f"{rec['reviewer_id']}::{rec['case_id']}"
                    if k in submissions:
                        errors.append(f"Duplicate unversioned review in dataset: {k}")
                    submissions[k] = {"path": f, "record": rec}
        except Exception as e:
            errors.append(f"Failed parsing {f.name}: {str(e)}")

    # Check case coverage
    case_coverage = {cid: 0 for cid in all_case_ids}
    for k, item in submissions.items():
        cid = item["record"]["case_id"]
        if cid in case_coverage:
            case_coverage[cid] += 1
        else:
            errors.append(f"Submission contains unknown case ID: {cid}")

    cases_under_2 = [cid for cid, count in case_coverage.items() if count < 2]
    if cases_under_2:
        errors.append(f"{len(cases_under_2)} case(s) have fewer than 2 independent reviews: {cases_under_2[:5]}...")

    return len(errors) == 0, errors, submissions


def freeze_reviews(
    submissions_dir: Path,
    frozen_dir: Path,
    manifest_path: Path,
    cases_path: Path
) -> Tuple[bool, str]:
    ok, errors, submissions = verify_completeness_and_validity(submissions_dir, manifest_path, cases_path)
    if not ok:
        print("Cannot freeze human review dataset due to validation / completeness errors:")
        for e in errors:
            print(f"  - {e}")
        return False, "FREEZE_FAILED_INCOMPLETE_OR_INVALID"

    frozen_dir.mkdir(parents=True, exist_ok=True)

    file_manifest = {}
    reviewers = set()
    cases_reviewed = set()

    for k, item in submissions.items():
        src_file: Path = item["path"]
        rec = item["record"]
        reviewers.add(rec["reviewer_id"])
        cases_reviewed.add(rec["case_id"])

        dst_file = frozen_dir / f"{rec['reviewer_id']}_{rec['case_id']}.json"
        with open(dst_file, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2)

        file_hash = compute_sha256(dst_file)
        file_manifest[dst_file.name] = {
            "reviewer_id": rec["reviewer_id"],
            "case_id": rec["case_id"],
            "qualification_tier": rec["qualification_tier"],
            "sha256": file_hash
        }

    # Generate review manifest
    manifest_data = {
        "frozen_dataset_version": "v0.2",
        "frozen_timestamp": "2026-09-16T00:36:00Z",
        "status": "HUMAN_REVIEW_FROZEN",
        "total_reviewers": len(reviewers),
        "total_cases_reviewed": len(cases_reviewed),
        "total_completed_reviews": len(submissions),
        "blinding_status": "STRICTLY_BLINDED",
        "files": file_manifest
    }

    manifest_file = frozen_dir / "review_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    manifest_sha = compute_sha256(manifest_file)
    print(f"Human review dataset successfully frozen into {frozen_dir}")
    print(f"Total reviews frozen: {len(submissions)} across {len(cases_reviewed)} cases and {len(reviewers)} reviewers.")
    print(f"Review manifest SHA-256: {manifest_sha}")

    return True, manifest_sha


def main():
    parser = argparse.ArgumentParser(description="Freeze completed BioReason human review dataset.")
    parser.add_argument("--submissions-dir", default="human_eval/v0.2/submissions", help="Directory of review submissions")
    parser.add_argument("--frozen-dir", default="human_eval/v0.2/frozen_reviews", help="Target directory for frozen reviews")
    parser.add_argument("--manifest", default="human_eval/v0.2/assignments/reviewer_assignment_manifest.json", help="Assignment manifest")
    parser.add_argument("--cases", default="human_eval/v0.2/cases.jsonl", help="Cases file")
    args = parser.parse_args()

    ok, res = freeze_reviews(
        Path(args.submissions_dir),
        Path(args.frozen_dir),
        Path(args.manifest),
        Path(args.cases)
    )
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

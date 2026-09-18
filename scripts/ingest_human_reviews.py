#!/usr/bin/env python3
"""
scripts/ingest_human_reviews.py

Ingests validated external human reviewer submissions into the official
BioReason v0.2 human evaluation tracking system.

Governance & Safety Rules:
1. Rejects duplicate submissions (same reviewer_id + same case_id) unless
   explicit versioned correction metadata is provided.
2. Writes validated submission files into human_eval/v0.2/submissions/
3. Generates/updates human_eval/v0.2/review_status.json with detailed technical completion metrics.
4. ABSOLUTE BLINDING: Never unblinds model identities during ingestion.
5. NEVER exposes or touches the locked final benchmark.
"""

import sys
import os
import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from validate_human_review_submission import validate_single_record, parse_csv_submission


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_existing_submissions(submissions_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    Loads all existing submissions from the official submissions directory.
    Keyed by '{reviewer_id}::{case_id}'.
    """
    existing = {}
    if not submissions_dir.exists():
        submissions_dir.mkdir(parents=True, exist_ok=True)
        return existing

    for f in submissions_dir.glob("*.json"):
        if f.name == "review_status.json" or f.name.startswith("audit_"):
            continue
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                if isinstance(data, list):
                    for rec in data:
                        k = f"{rec['reviewer_id']}::{rec['case_id']}"
                        existing[k] = {"file": f.name, "record": rec}
                elif isinstance(data, dict):
                    k = f"{data['reviewer_id']}::{data['case_id']}"
                    existing[k] = {"file": f.name, "record": data}
        except Exception as e:
            print(f"Warning: Failed reading existing submission file {f}: {e}")

    return existing


def update_review_status(
    submissions: Dict[str, Dict[str, Any]],
    manifest_path: Path,
    cases_path: Path,
    output_path: Path,
    corrections_log: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Computes technical coverage metrics and writes review_status.json."""
    # Load manifest and cases
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    all_cases = {}
    with open(cases_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                all_cases[item["case_id"]] = item

    total_expected = manifest.get("total_case_reviews_planned", 117)
    completed_count = len(submissions)
    remaining_count = max(0, total_expected - completed_count)

    # Reviews per case
    case_review_counts = {cid: 0 for cid in all_cases}
    for k, item in submissions.items():
        cid = item["record"]["case_id"]
        if cid in case_review_counts:
            case_review_counts[cid] += 1

    cases_0 = sum(1 for c, n in case_review_counts.items() if n == 0)
    cases_1 = sum(1 for c, n in case_review_counts.items() if n == 1)
    cases_2plus = sum(1 for c, n in case_review_counts.items() if n >= 2)

    # Reviewer completion stats
    reviewer_stats = {}
    for r in manifest.get("reviewers", []):
        r_id = r["reviewer_id"]
        assigned = manifest.get("reviewer_workload", {}).get(r_id, 0)
        done = sum(1 for k in submissions if k.startswith(f"{r_id}::"))
        reviewer_stats[r_id] = {
            "qualification_tier": r["qualification_tier"],
            "assigned_cases": assigned,
            "completed_cases": done,
            "pending_cases": max(0, assigned - done),
            "completion_pct": round((done / assigned * 100) if assigned > 0 else 0.0, 1)
        }

    # Domain coverage
    domain_coverage = {}
    for cid, cdata in all_cases.items():
        dom = cdata.get("domain", "unknown")
        if dom not in domain_coverage:
            domain_coverage[dom] = {"total_cases": 0, "reviews_collected": 0}
        domain_coverage[dom]["total_cases"] += 1
        domain_coverage[dom]["reviews_collected"] += case_review_counts[cid]

    # Overall State
    if completed_count == 0:
        overall_status = "PACKAGE_READY"
    elif cases_0 == 0 and cases_1 == 0 and completed_count >= total_expected:
        overall_status = "HUMAN_REVIEW_COMPLETE_UNFROZEN"
    else:
        overall_status = "HUMAN_REVIEW_INCOMPLETE"

    status_data = {
        "status": overall_status,
        "human_review_phase": "Phase 3 Increment 8B",
        "total_cases": len(all_cases),
        "total_expected_reviews": total_expected,
        "completed_reviews": completed_count,
        "remaining_reviews": remaining_count,
        "overall_completion_pct": round((completed_count / total_expected * 100), 1),
        "coverage_by_case": {
            "cases_with_0_reviews": cases_0,
            "cases_with_1_review": cases_1,
            "cases_with_2plus_reviews": cases_2plus
        },
        "reviewer_completion": reviewer_stats,
        "domain_coverage": domain_coverage,
        "corrections_logged": len(corrections_log),
        "last_updated": "2026-09-16T00:35:00Z"
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=2)

    return status_data


def ingest_records(
    records: List[Dict[str, Any]],
    submissions_dir: Path,
    manifest_assignments: Dict[str, List[str]],
    allow_correction: bool = False,
    correction_reason: Optional[str] = None
) -> Tuple[int, int, List[str]]:
    """Ingests records with strict validation and duplicate rejection."""
    existing = load_existing_submissions(submissions_dir)
    corrections_path = submissions_dir / "audit_corrections.json"
    corrections_log = []
    if corrections_path.exists():
        try:
            with open(corrections_path, "r", encoding="utf-8") as f:
                corrections_log = json.load(f)
        except Exception:
            pass

    ingested = 0
    rejected = 0
    errors = []

    for idx, rec in enumerate(records):
        ok, errs = validate_single_record(rec, manifest_assignments)
        if not ok:
            rejected += 1
            errors.append(f"Record {idx + 1} validation failed: {'; '.join(errs)}")
            continue

        r_id = rec["reviewer_id"]
        c_id = rec["case_id"]
        key = f"{r_id}::{c_id}"

        if key in existing:
            if not allow_correction:
                rejected += 1
                errors.append(f"Duplicate submission rejected for {r_id} on {c_id}. Must specify --allow-correction with reason.")
                continue
            else:
                # Log versioned correction
                old_rec = existing[key]["record"]
                old_hash = compute_sha256(json.dumps(old_rec, sort_keys=True).encode("utf-8"))
                new_hash = compute_sha256(json.dumps(rec, sort_keys=True).encode("utf-8"))
                correction_entry = {
                    "reviewer_id": r_id,
                    "case_id": c_id,
                    "previous_hash": old_hash,
                    "new_hash": new_hash,
                    "reason": correction_reason or "Reviewer correction prior to freeze",
                    "timestamp": rec.get("submitted_at")
                }
                corrections_log.append(correction_entry)
                with open(corrections_path, "w", encoding="utf-8") as f:
                    json.dump(corrections_log, f, indent=2)

        # Write individual submission file
        out_file = submissions_dir / f"{r_id}_{c_id}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2)

        existing[key] = {"file": out_file.name, "record": rec}
        ingested += 1

    return ingested, rejected, errors


def main():
    parser = argparse.ArgumentParser(description="Ingest human review submissions into BioReason tracking system.")
    parser.add_argument("input_path", help="Path to validated submission JSON file, CSV file, or directory")
    parser.add_argument("--submissions-dir", default="human_eval/v0.2/submissions", help="Target submissions directory")
    parser.add_argument("--manifest", default="human_eval/v0.2/assignments/reviewer_assignment_manifest.json", help="Path to assignment manifest")
    parser.add_argument("--cases", default="human_eval/v0.2/cases.jsonl", help="Path to cases.jsonl")
    parser.add_argument("--status-file", default="human_eval/v0.2/review_status.json", help="Path to output review_status.json")
    parser.add_argument("--allow-correction", action="store_true", help="Permit updating an existing review with a versioned correction")
    parser.add_argument("--correction-reason", default=None, help="Reason for review correction")
    args = parser.parse_args()

    submissions_dir = Path(args.submissions_dir)
    submissions_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(args.manifest)
    cases_path = Path(args.cases)
    status_path = Path(args.status_file)

    manifest_assignments = {}
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            man = json.load(f)
            for r in man.get("reviewers", []):
                manifest_assignments[r["reviewer_id"]] = []
            for cid, revs in man.get("case_assignments", {}).items():
                for r_id in revs:
                    if r_id in manifest_assignments:
                        manifest_assignments[r_id].append(cid)

    input_path = Path(args.input_path)
    records = []
    if input_path.is_file():
        if input_path.suffix == ".json":
            with open(input_path, "r", encoding="utf-8") as f:
                d = json.load(f)
                records = d if isinstance(d, list) else [d]
        elif input_path.suffix == ".csv":
            records = parse_csv_submission(input_path)
    elif input_path.is_dir():
        for f in list(input_path.glob("*.json")) + list(input_path.glob("*.csv")):
            if f.suffix == ".json":
                with open(f, "r", encoding="utf-8") as fp:
                    d = json.load(fp)
                    records.extend(d if isinstance(d, list) else [d])
            elif f.suffix == ".csv":
                records.extend(parse_csv_submission(f))

    if not records:
        print(f"No records found in {input_path}")
        # Still update status for initial state
        existing = load_existing_submissions(submissions_dir)
        st = update_review_status(existing, manifest_path, cases_path, status_path, [])
        print(f"Updated status: {st['status']} ({st['completed_reviews']}/{st['total_expected_reviews']} complete)")
        sys.exit(0)

    ingested, rejected, errors = ingest_records(
        records, submissions_dir, manifest_assignments,
        allow_correction=args.allow_correction,
        correction_reason=args.correction_reason
    )

    existing = load_existing_submissions(submissions_dir)
    corrections_path = submissions_dir / "audit_corrections.json"
    corrections_log = []
    if corrections_path.exists():
        with open(corrections_path, "r", encoding="utf-8") as f:
            corrections_log = json.load(f)

    status = update_review_status(existing, manifest_path, cases_path, status_path, corrections_log)

    print(f"Ingested: {ingested} submissions.")
    print(f"Rejected: {rejected} submissions.")
    if errors:
        print("Rejection details:")
        for err in errors:
            print(f"  - {err}")

    print(f"\nCurrent Human Review Status: {status['status']}")
    print(f"Completion: {status['completed_reviews']} / {status['total_expected_reviews']} ({status['overall_completion_pct']}%)")
    print(f"Cases with >= 2 reviews: {status['coverage_by_case']['cases_with_2plus_reviews']} / {status['total_cases']}")


if __name__ == "__main__":
    main()

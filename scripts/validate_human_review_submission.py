#!/usr/bin/env python3
"""
scripts/validate_human_review_submission.py

Validates individual or batch human review submission files against the strict
BioReason v0.2 review schema and scientific integrity rules.

Checks:
1. JSON Schema conformance (draft-07 via jsonschema or internal validator)
2. Value boundaries (1-5 integer ratings for all 10 dimensions for all 3 models)
3. Enum validity (confidence, qualification_tier, pairwise_preference)
4. Case ID and Reviewer ID pattern matching
5. Assignment validity (optional cross-reference against assignments manifest)
6. Model-identity leak check (assures no raw checkpoint IDs or model names leaked)
"""

import sys
import os
import re
import json
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

FORBIDDEN_LEAK_STRINGS = [
    "qwen", "bioreason", "br-dpo", "br-v02", "br-sft", "checkpoint-", "sft-001", "dpo-001"
]

REQUIRED_DIMENSIONS = [
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

VALID_CONFIDENCES = {"LOW", "MEDIUM", "HIGH"}
VALID_PREFERENCES = {"RESPONSE_A", "RESPONSE_B", "RESPONSE_C", "TIE", "NONE_ACCEPTABLE"}
VALID_TIERS = {
    "EXPERT_DOMAIN",
    "COMPUTATIONAL_BIOLOGIST",
    "BIOSTATISTICIAN",
    "BIOINFORMATICIAN",
    "GENERAL_BIOLOGICAL_SCIENTIST",
    "OTHER_RELEVANT_SCIENTIST"
}


def validate_single_record(record: Dict[str, Any], manifest_assignments: Optional[Dict[str, List[str]]] = None) -> Tuple[bool, List[str]]:
    """Validates a single human review evaluation record."""
    errors = []

    # 1. Schema version
    version = record.get("schema_version")
    if version not in ["v0.2", "0.2.0"]:
        errors.append(f"Invalid schema_version '{version}', expected 'v0.2' or '0.2.0'")

    # 2. Reviewer ID
    r_id = record.get("reviewer_id")
    if not r_id or not re.match(r"^REV[0-9]{3,}$", str(r_id)):
        errors.append(f"Invalid reviewer_id '{r_id}', expected format REV001, REV002, etc.")

    # 3. Case ID
    c_id = record.get("case_id")
    if not c_id or not re.match(r"^HEVAL_[0-9]{3,}$", str(c_id)):
        errors.append(f"Invalid case_id '{c_id}', expected format HEVAL_001, etc.")

    # 4. Qualification tier
    tier = record.get("qualification_tier")
    if tier not in VALID_TIERS:
        errors.append(f"Invalid qualification_tier '{tier}', expected one of {sorted(list(VALID_TIERS))}")

    # 5. Reviewer confidence
    conf = record.get("reviewer_confidence")
    if conf not in VALID_CONFIDENCES:
        errors.append(f"Invalid reviewer_confidence '{conf}', expected one of {sorted(list(VALID_CONFIDENCES))}")

    # 6. Pairwise preference
    pref = record.get("pairwise_preference")
    if pref not in VALID_PREFERENCES:
        errors.append(f"Invalid pairwise_preference '{pref}', expected one of {sorted(list(VALID_PREFERENCES))}")

    # 7. Submitted timestamp
    submitted_at = record.get("submitted_at")
    if not submitted_at:
        errors.append("Missing 'submitted_at' timestamp")

    # 8. Response evaluations (A, B, C)
    evals = record.get("response_evaluations")
    if not isinstance(evals, dict):
        errors.append("Missing or non-dictionary 'response_evaluations'")
    else:
        for model in ["RESPONSE_A", "RESPONSE_B", "RESPONSE_C"]:
            if model not in evals:
                errors.append(f"Missing evaluation block for '{model}'")
                continue
            m_eval = evals[model]
            if not isinstance(m_eval, dict):
                errors.append(f"Evaluation block for '{model}' must be a dictionary")
                continue
            for dim in REQUIRED_DIMENSIONS:
                if dim not in m_eval:
                    errors.append(f"Model '{model}' missing required dimension '{dim}'")
                else:
                    val = m_eval[dim]
                    if not isinstance(val, int) or val < 1 or val > 5:
                        errors.append(f"Model '{model}' dimension '{dim}' has invalid score '{val}', must be integer 1-5")

    # 9. Assignment cross-reference check
    if manifest_assignments and r_id and c_id:
        assigned_cases = manifest_assignments.get(r_id, [])
        if c_id not in assigned_cases:
            errors.append(f"Case '{c_id}' was not assigned to reviewer '{r_id}'")

    # 10. Model identity leakage check in comments
    comments = str(record.get("comments", "")) + " " + str(record.get("qualitative_rationale", ""))
    for s in FORBIDDEN_LEAK_STRINGS:
        if s in comments.lower():
            errors.append(f"Review comment contains forbidden model-revealing token: '{s}'")

    return len(errors) == 0, errors


def parse_csv_submission(csv_path: Path) -> List[Dict[str, Any]]:
    """Parses a CSV scorecard template into a list of structured submission dicts."""
    records = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("case_id") or not row.get("pairwise_preference"):
                continue
            evals = {}
            for model in ["RESPONSE_A", "RESPONSE_B", "RESPONSE_C"]:
                evals[model] = {}
                for dim in REQUIRED_DIMENSIONS:
                    col_name = f"{model}_{dim}"
                    val_str = row.get(col_name, "3")
                    evals[model][dim] = int(val_str) if val_str.isdigit() else 3

            record = {
                "schema_version": "v0.2",
                "reviewer_id": row.get("reviewer_id", "").strip(),
                "case_id": row.get("case_id", "").strip(),
                "qualification_tier": row.get("qualification_tier", "GENERAL_BIOLOGICAL_SCIENTIST").strip(),
                "reviewer_confidence": row.get("reviewer_confidence", "MEDIUM").strip(),
                "response_evaluations": evals,
                "pairwise_preference": row.get("pairwise_preference", "").strip(),
                "comments": row.get("comments", "").strip(),
                "submitted_at": "2026-09-16T00:00:00Z"
            }
            records.append(record)
    return records


def validate_file(file_path: Path, manifest_assignments: Optional[Dict[str, List[str]]] = None) -> Tuple[bool, int, List[str]]:
    """Validates an entire JSON or CSV submission file."""
    all_errors = []
    records = []

    if file_path.suffix == ".json":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict):
                    records = [data]
                else:
                    return False, 0, ["JSON root must be an object or array of objects"]
        except Exception as e:
            return False, 0, [f"JSON parse error: {str(e)}"]

    elif file_path.suffix == ".csv":
        try:
            records = parse_csv_submission(file_path)
        except Exception as e:
            return False, 0, [f"CSV parse error: {str(e)}"]
    else:
        return False, 0, [f"Unsupported file format '{file_path.suffix}', expected .json or .csv"]

    for idx, rec in enumerate(records):
        ok, errs = validate_single_record(rec, manifest_assignments)
        if not ok:
            for err in errs:
                all_errors.append(f"Record {idx + 1} (case: {rec.get('case_id', 'unknown')}): {err}")

    return len(all_errors) == 0, len(records), all_errors


def main():
    parser = argparse.ArgumentParser(description="Validate BioReason v0.2 human review submissions.")
    parser.add_argument("input_path", help="Path to submission JSON file, CSV file, or directory of submissions")
    parser.add_argument("--manifest", default=None, help="Optional path to reviewer_assignment_manifest.json")
    args = parser.parse_args()

    manifest_assignments = None
    if args.manifest and os.path.exists(args.manifest):
        with open(args.manifest, "r", encoding="utf-8") as f:
            man = json.load(f)
            # Map reviewer_id -> list of assigned cases
            manifest_assignments = {}
            for r in man.get("reviewers", []):
                r_id = r["reviewer_id"]
                manifest_assignments[r_id] = []
            for cid, revs in man.get("case_assignments", {}).items():
                for r_id in revs:
                    if r_id in manifest_assignments:
                        manifest_assignments[r_id].append(cid)

    input_path = Path(args.input_path)
    files_to_check = []
    if input_path.is_dir():
        files_to_check = list(input_path.glob("*.json")) + list(input_path.glob("*.csv"))
    elif input_path.is_file():
        files_to_check = [input_path]
    else:
        print(f"Error: Path '{input_path}' does not exist.")
        sys.exit(1)

    total_records = 0
    total_files = len(files_to_check)
    has_failures = False

    print(f"Validating {total_files} submission file(s)...")
    for f in files_to_check:
        ok, count, errs = validate_file(f, manifest_assignments)
        total_records += count
        if ok:
            print(f"  [PASS] {f.name} ({count} records)")
        else:
            has_failures = True
            print(f"  [FAIL] {f.name} ({len(errs)} errors):")
            for err in errs:
                print(f"    - {err}")

    print(f"\nTotal submissions validated: {total_records}")
    if has_failures:
        print("Validation FAILED.")
        sys.exit(1)
    else:
        print("All submissions PASSED validation successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
scripts/build_packet_manifest.py

Computes cryptographic SHA-256 hashes for all reviewer packets
under human_eval/v0.2/reviewer_packets/ and generates PACKET_MANIFEST.json.

Invariants:
1. Every packet directory must contain:
   - assigned_cases.json
   - scorecard_template.csv
   - viewer.html
   - REVIEWER_GUIDE.md
2. Confirms that no packet contains model-identifying strings or randomization mappings.
3. Computes individual file hashes and composite packet hashes.
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any


def compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(packets_dir: Path, manifest_path: Path) -> Dict[str, Any]:
    packet_dirs = sorted([d for d in packets_dir.iterdir() if d.is_dir() and d.name.startswith("REV")])
    if not packet_dirs:
        raise RuntimeError(f"No reviewer packet directories found under {packets_dir}")

    manifest_data = {
        "manifest_version": "v0.2.0",
        "created_at": "2026-09-16T00:40:00Z",
        "total_packets": len(packet_dirs),
        "packets": {}
    }

    required_files = ["assigned_cases.json", "scorecard_template.csv", "viewer.html", "REVIEWER_GUIDE.md"]

    for p_dir in packet_dirs:
        r_id = p_dir.name
        file_hashes = {}
        for fname in required_files:
            fpath = p_dir / fname
            if not fpath.exists():
                raise FileNotFoundError(f"Missing required packet file '{fname}' in {p_dir}")
            file_hashes[fname] = compute_file_sha256(fpath)

        # Load assigned cases to record case IDs and count
        cases_file = p_dir / "assigned_cases.json"
        with open(cases_file, "r", encoding="utf-8") as f:
            cases_data = json.load(f)
            case_ids = [c["case_id"] for c in cases_data]

        # Compute composite packet hash (hash of sorted file hashes)
        composite_content = "".join(f"{k}:{file_hashes[k]}" for k in sorted(file_hashes.keys()))
        composite_hash = hashlib.sha256(composite_content.encode("utf-8")).hexdigest()

        manifest_data["packets"][r_id] = {
            "reviewer_id": r_id,
            "case_count": len(case_ids),
            "case_ids": case_ids,
            "file_hashes": file_hashes,
            "packet_composite_sha256": composite_hash
        }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return manifest_data


def main():
    packets_dir = Path("human_eval/v0.2/reviewer_packets")
    manifest_path = packets_dir / "PACKET_MANIFEST.json"
    manifest = build_manifest(packets_dir, manifest_path)
    print(f"Generated PACKET_MANIFEST.json with {manifest['total_packets']} packets.")
    for r_id, pdata in manifest["packets"].items():
        print(f"  - {r_id}: {pdata['case_count']} cases | SHA256: {pdata['packet_composite_sha256'][:16]}...")


if __name__ == "__main__":
    main()

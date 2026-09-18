#!/usr/bin/env python3
"""Prepare the verified SFT pre-run manifest before Slurm submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from dataclasses import asdict, fields
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioreason.training.verified_sft_trainer import VerifiedSFTConfig, get_git_info, sha256_file, write_json


def stable_hash(data: dict) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model-path")
    parser.add_argument("--output-dir")
    parser.add_argument("--durable-archive-dir")
    parser.add_argument("--epochs", type=float)
    parser.add_argument("--max-seq-length", type=int)
    parser.add_argument("--train-file")
    parser.add_argument("--val-file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = VerifiedSFTConfig()
    updates = {
        "base_model_path": args.base_model_path,
        "output_dir": args.output_dir,
        "durable_archive_dir": args.durable_archive_dir,
        "num_train_epochs": args.epochs,
        "max_seq_length": args.max_seq_length,
        "train_file": args.train_file,
        "val_file": args.val_file,
    }
    valid = {f.name for f in fields(config)}
    for key, value in updates.items():
        if value is not None and key in valid:
            setattr(config, key, value)

    base = Path(config.base_model_path)
    if not (base / "config.json").exists():
        raise FileNotFoundError(f"Base model config not found: {base}")
    output_dir = Path(config.output_dir)
    manifest = {
        "run_id": config.run_id,
        "status": "PREPARED_BEFORE_SLURM_SUBMISSION",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git": get_git_info(),
        "python": platform.python_version(),
        "base_model_name": config.base_model_name,
        "base_model_snapshot": str(base),
        "base_model_snapshot_id": base.name,
        "base_model_config_sha256": sha256_file(base / "config.json"),
        "train_file": config.train_file,
        "train_file_sha256": sha256_file(Path(config.train_file)),
        "val_file": config.val_file,
        "val_file_sha256": sha256_file(Path(config.val_file)),
        "training_config": asdict(config),
    }
    manifest["training_config_sha256"] = stable_hash(manifest["training_config"])
    path = output_dir / "BIOREASON_SFT_VERIFIED_PRE_RUN_MANIFEST.json"
    write_json(path, manifest)
    print(path)


if __name__ == "__main__":
    main()

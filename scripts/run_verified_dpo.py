#!/usr/bin/env python3
"""Run the first verified BioReason DPO training path (BR-VERIFIED-SFT-002 -> BR-VERIFIED-DPO-001)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import fields
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioreason.training.verified_dpo_trainer import VerifiedDPOConfig, train_verified_dpo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model-path")
    parser.add_argument("--parent-adapter-path")
    parser.add_argument("--output-dir")
    parser.add_argument("--durable-archive-dir")
    parser.add_argument("--train-file")
    parser.add_argument("--val-file")
    parser.add_argument("--run-id")
    parser.add_argument("--epochs", type=float)
    parser.add_argument("--learning-rate", type=float)
    parser.add_argument("--beta", type=float)
    parser.add_argument("--gradient-accumulation-steps", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = VerifiedDPOConfig()
    updates = {
        "base_model_path": args.base_model_path,
        "parent_adapter_path": args.parent_adapter_path,
        "output_dir": args.output_dir,
        "durable_archive_dir": args.durable_archive_dir,
        "train_file": args.train_file,
        "val_file": args.val_file,
        "run_id": args.run_id,
        "num_train_epochs": args.epochs,
        "learning_rate": args.learning_rate,
        "beta": args.beta,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
    }
    valid = {f.name for f in fields(config)}
    for key, value in updates.items():
        if value is not None and key in valid:
            setattr(config, key, value)
    result = train_verified_dpo(config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

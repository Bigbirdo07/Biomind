#!/usr/bin/env python3
"""Run the first verified BioReason LoRA SFT training path."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import fields
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioreason.training.verified_sft_trainer import VerifiedSFTConfig, train_verified_sft


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model-path")
    parser.add_argument("--output-dir")
    parser.add_argument("--durable-archive-dir")
    parser.add_argument("--epochs", type=float)
    parser.add_argument("--max-seq-length", type=int)
    parser.add_argument("--train-file")
    parser.add_argument("--val-file")
    parser.add_argument("--run-id")
    parser.add_argument("--train-format", choices=["legacy_episode", "messages"])
    parser.add_argument("--assistant-only-label-masking", action="store_true", default=None)
    parser.add_argument("--learning-rate", type=float)
    parser.add_argument("--lora-r", type=int)
    parser.add_argument("--lora-alpha", type=int)
    parser.add_argument("--resume-adapter-path")
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
        "run_id": args.run_id,
        "train_format": args.train_format,
        "assistant_only_label_masking": args.assistant_only_label_masking,
        "learning_rate": args.learning_rate,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "resume_adapter_path": args.resume_adapter_path,
    }
    valid = {f.name for f in fields(config)}
    for key, value in updates.items():
        if value is not None and key in valid:
            setattr(config, key, value)
    result = train_verified_sft(config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run deterministic real Qwen baseline inference for Phase T1."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import fields
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioreason.training.verified_eval import VerifiedEvalConfig, run_verified_baseline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model-path")
    parser.add_argument("--adapter-path")
    parser.add_argument("--run-id")
    parser.add_argument("--output-dir")
    parser.add_argument("--dev-file")
    parser.add_argument("--regression-file")
    parser.add_argument("--max-items", type=int)
    parser.add_argument("--max-new-tokens", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = VerifiedEvalConfig()
    updates = {
        "base_model_path": args.base_model_path,
        "adapter_path": args.adapter_path,
        "run_id": args.run_id,
        "output_dir": args.output_dir,
        "dev_file": args.dev_file,
        "regression_file": args.regression_file,
        "max_items": args.max_items,
    }
    valid = {f.name for f in fields(config)}
    for key, value in updates.items():
        if value is not None and key in valid:
            setattr(config, key, value)
    if args.max_new_tokens is not None:
        config.generation.max_new_tokens = args.max_new_tokens
    result = run_verified_baseline(config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

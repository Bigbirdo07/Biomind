#!/usr/bin/env python3
"""Run real mode-conditioned inference (router + overlays) over a conversation item set."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import fields
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioreason.training.verified_mode_conditioned_eval import ModeConditionedEvalConfig, run_mode_conditioned_eval


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model-path")
    parser.add_argument("--adapter-path")
    parser.add_argument("--run-id")
    parser.add_argument("--output-dir")
    parser.add_argument("--items-file")
    parser.add_argument("--max-new-tokens", type=int)
    parser.add_argument("--router-max-new-tokens", type=int)
    parser.add_argument("--disable-two-pass-audit", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ModeConditionedEvalConfig()
    updates = {
        "base_model_path": args.base_model_path,
        "adapter_path": args.adapter_path,
        "run_id": args.run_id,
        "output_dir": args.output_dir,
        "items_file": args.items_file,
        "router_max_new_tokens": args.router_max_new_tokens,
    }
    valid = {f.name for f in fields(config)}
    for key, value in updates.items():
        if value is not None and key in valid:
            setattr(config, key, value)
    if args.max_new_tokens is not None:
        config.generation.max_new_tokens = args.max_new_tokens
    if args.disable_two_pass_audit:
        config.enable_two_pass_audit = False
    result = run_mode_conditioned_eval(config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

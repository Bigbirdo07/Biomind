#!/usr/bin/env python3
"""Run mode-conditioned inference (router + overlays) over Dev/Regression."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import fields
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioreason.training.verified_mode_conditioned_eval import (
    ModeConditionedDevRegressionConfig,
    run_mode_conditioned_dev_regression,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model-path")
    parser.add_argument("--adapter-path")
    parser.add_argument("--run-id")
    parser.add_argument("--output-dir")
    parser.add_argument("--dev-file")
    parser.add_argument("--regression-file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ModeConditionedDevRegressionConfig()
    updates = {
        "base_model_path": args.base_model_path,
        "adapter_path": args.adapter_path,
        "run_id": args.run_id,
        "output_dir": args.output_dir,
        "dev_file": args.dev_file,
        "regression_file": args.regression_file,
    }
    valid = {f.name for f in fields(config)}
    for key, value in updates.items():
        if value is not None and key in valid:
            setattr(config, key, value)
    result = run_mode_conditioned_dev_regression(config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run real multi-turn conversational inference over BioReasonConversationDev-v0.1."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import fields
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioreason.training.verified_conversation_eval import ConversationEvalConfig, run_conversation_eval


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model-path")
    parser.add_argument("--adapter-path")
    parser.add_argument("--run-id")
    parser.add_argument("--output-dir")
    parser.add_argument("--items-file")
    parser.add_argument("--system-prompt")
    parser.add_argument("--max-new-tokens", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ConversationEvalConfig()
    updates = {
        "base_model_path": args.base_model_path,
        "adapter_path": args.adapter_path,
        "run_id": args.run_id,
        "output_dir": args.output_dir,
        "items_file": args.items_file,
        "system_prompt": args.system_prompt,
    }
    valid = {f.name for f in fields(config)}
    for key, value in updates.items():
        if value is not None and key in valid:
            setattr(config, key, value)
    if args.max_new_tokens is not None:
        config.generation.max_new_tokens = args.max_new_tokens
    result = run_conversation_eval(config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

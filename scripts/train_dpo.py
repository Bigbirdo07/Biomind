"""
Entry point for BioReason Direct Preference Optimization (BR-DPO-001).
"""

import argparse
import sys
from pathlib import Path
import yaml

from bioreason.training.dpo_trainer import DPOConfig, ScientificDPOTrainer


def main():
    parser = argparse.ArgumentParser(description="Train BioReason via Direct Preference Optimization (DPO)")
    parser.add_argument("--config", type=str, default="configs/training/br_dpo_001.yaml", help="Path to DPO config YAML")
    parser.add_argument("--smoke-test", action="store_true", help="Run DPO smoke test on subset of preference pairs")
    parser.add_argument("--num-pairs", type=int, default=50, help="Number of preference pairs for smoke test")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    dpo_config = DPOConfig(**config_data)
    trainer = ScientificDPOTrainer(dpo_config)

    res = trainer.train_smoke_test(num_pairs=args.num_pairs)
    print(f"\n[DPO Pipeline Status]: {res['status']}")
    print(f"Checkpoints created at: {res['checkpoint_dir']}")


if __name__ == "__main__":
    main()

"""
HPC Training script for BioReason Phase 0.
"""

import argparse
import sys
from pathlib import Path
import yaml

from bioreason.training.config import TrainingConfig
from bioreason.training.sft_trainer import ScientificSFTTrainer


def main():
    parser = argparse.ArgumentParser(description="Train BioReason via SFT (LoRA/QLoRA)")
    parser.add_argument("--config", type=str, required=True, help="Path to training config YAML")
    parser.add_argument("--dry-run", action="store_true", help="Run smoke test without GPU training")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    training_config = TrainingConfig.model_validate(config_data)
    trainer = ScientificSFTTrainer(training_config)

    print(f"Initializing BioReason SFT Trainer for model: {training_config.model_name_or_path}")
    print(f"Dataset path: {training_config.train_dataset_path}")
    print(f"Output directory: {training_config.output_dir}")

    res = trainer.train_smoke_test()
    print(f"Smoke test successful: {res['samples_formatted']} samples formatted and verified.")
    print(f"Run manifest generated at: {res['output_directory']}/run_manifest.json")


if __name__ == "__main__":
    main()

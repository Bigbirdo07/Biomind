"""
HPC Training script for BioReason Phase 2 Supervised Fine-Tuning (BR-SFT-001).
Compatible with UMass Unity HPC execution with pre-cached local models and LoRA adapters.
"""

import argparse
import sys
from pathlib import Path
import yaml

from bioreason.training.config import TrainingConfig
from bioreason.training.sft_trainer import ScientificSFTTrainer


def main():
    parser = argparse.ArgumentParser(description="Train BioReason via SFT (LoRA/QLoRA)")
    parser.add_argument("--config", type=str, default="configs/training/br_sft_001_a.yaml", help="Path to training config YAML")
    parser.add_argument("--model-path", type=str, default=None, help="Explicit path to pre-cached base model weights on Unity")
    parser.add_argument("--smoke-test", action="store_true", help="Execute a fast smoke training run (50-100 examples)")
    parser.add_argument("--num-examples", type=int, default=50, help="Number of examples to use in smoke test")
    parser.add_argument("--dry-run", action="store_true", help="Alias for smoke test without full GPU training")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    if args.model_path:
        config_data["model_name_or_path"] = args.model_path

    training_config = TrainingConfig.model_validate(config_data)
    trainer = ScientificSFTTrainer(training_config)

    print(f"==================================================")
    print(f"BioReason Phase 2 SFT Engine")
    print(f"Experiment: {training_config.experiment_name}")
    print(f"Base Model: {training_config.model_name_or_path}")
    print(f"Dataset Path: {training_config.train_dataset_path}")
    print(f"Output Directory: {training_config.output_dir}")
    print(f"Selected Tiers: {training_config.selected_tiers}")
    print(f"Tier Weights: {training_config.tier_weights}")
    print(f"==================================================")

    # Display weighting diagnostic
    loss_diag = trainer.compute_weighted_loss_diagnostic()
    print(f"Example Loss Weighting Diagnostic:")
    print(f"- Total Samples: {loss_diag['total_samples']}")
    print(f"- Effective Loss Weight: {loss_diag['total_effective_weight']}")
    for tier, tdata in loss_diag["tier_diagnostics"].items():
        print(f"  * {tier}: count={tdata['count']}, nominal_weight={tdata['nominal_weight']}, loss_share={tdata['relative_loss_share']*100:.2f}%")
    print(f"==================================================")

    if args.smoke_test or args.dry_run:
        print(f"Executing Smoke Training Run ({args.num_examples} samples)...")
        res = trainer.train_smoke_test(num_examples=args.num_examples)
        print(f"\n[SUCCESS] Smoke SFT Completed:")
        print(f"- Samples Trained: {res['samples_trained']}")
        print(f"- Loss Trajectory: Initial {res['initial_loss']} -> Final {res['final_loss']}")
        print(f"- Total Tokens: {res['total_tokens']}")
        print(f"- Checkpoint Directory: {res['checkpoint_dir']}")
        print(f"- Run Manifest: {res['manifest_path']}")
    else:
        print(f"Executing Full SFT Training across all milestones...")
        res = trainer.train_full_experiment()
        print(f"\n[SUCCESS] Full SFT Training Completed:")
        print(f"- Total Train Samples: {res['total_train_samples']}")
        print(f"- Total Tokens: {res['total_tokens']}")
        print(f"- Final Train Loss: {res['final_train_loss']} | Val Loss: {res['final_val_loss']}")
        print(f"- Total Checkpoints Saved: {len(res['checkpoints'])}")
        for ckpt in res["checkpoints"]:
            print(f"  * Epoch {ckpt['epoch']}: TrainLoss={ckpt['train_loss']}, ValLoss={ckpt['val_loss']}, Dir={ckpt['checkpoint_dir']}")
        print(f"- Master Run Manifest: {res['manifest_path']}")


if __name__ == "__main__":
    main()

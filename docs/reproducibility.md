# Reproducibility & Provenance Tracking

In scientific machine learning, an experiment without complete provenance is untraceable and irreproducible.

Every training run in BioReason automatically writes a machine-readable `run_manifest.json` in the run output directory.

---

## Provenance Manifest Schema

```json
{
  "run_id": "bioreason_run_1773676800",
  "timestamp": "2026-09-15 16:00:00 UTC",
  "git_commit": "a1b2c3d4e5f6...",
  "git_dirty": false,
  "model_name": "meta-llama/Meta-Llama-3-8B-Instruct",
  "model_revision": "main",
  "tokenizer_revision": "main",
  "dataset_version": "BioReasonTrain_v0.1 (20 episodes)",
  "benchmark_version": "BioReasonBench_v0.1",
  "training_config": {
    "peft_method": "qlora",
    "learning_rate": 0.0002,
    "num_train_epochs": 3,
    "max_seq_length": 2048,
    "seed": 42
  },
  "random_seed": 42,
  "learning_rate": 0.0002,
  "optimizer": "adamw_torch",
  "scheduler": "cosine",
  "precision": "bf16",
  "gpu_count": 1,
  "checkpoint_path": "outputs/run_001/final_checkpoint",
  "evaluation_metrics": {
    "benchmark_composite_score": 0.842,
    "flaw_detection_accuracy": 0.95
  }
}
```

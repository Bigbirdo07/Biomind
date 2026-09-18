# BioReason v0.1 Reproducibility Manifest & Environment Specification

This document provides the exact environment, dataset hashes, model configurations, and cryptographic checkpoints required to reproduce BioReason v0.1.

---

## 1. Cryptographic Hashes & Provenance

| Component | Identifier / Path | Cryptographic Hash (SHA-256) |
| :--- | :--- | :--- |
| **Git Commit** | `29bdb05590a56618970576e746bfccdfe8583ced` (Branch: `main`) | Verified clean working tree |
| **Benchmark (BioReasonBench-v0.1)** | `benchmark/frozen/bioreasonbench_v0.1/` (340 items) | `ae2d65aa71f735c24c7781ffac74fe8fe0c97a972b20cc781e75dea42ff2cfad` |
| **SFT Training Dataset** | `training_data/snapshots/bioreasontrain_sft_v0.1/` (1,120 episodes) | `9e25d1bad9d9d86cb037655314b9bab10671a5478511801ab1b272728e893547` |
| **Preference Dataset** | `training_data/preferences/bioreason_preference_v0.2/` (245 pairs) | `3cb1e15ff24030a19b2c77fa7762227043a298d1a57e69293f27fae710a71b1d` |
| **Parent SFT Checkpoint** | `outputs/BR-SFT-001-A/checkpoint-epoch-2.0` | PEFT LoRA adapter checkpoint |
| **Selected DPO Checkpoint** | `outputs/BR-DPO-002-A/checkpoint-100pct` | PEFT LoRA adapter checkpoint |

---

## 2. Software & Python Environment
- **Python**: 3.12.2 (CPython)
- **PyTorch**: `>=2.1.0`
- **HuggingFace Transformers**: `>=4.40.0`
- **PEFT**: `>=0.10.0`
- **TRL (Transformer Reinforcement Learning)**: `>=0.8.0`
- **Pydantic**: `>=2.0.0`
- **Pytest**: `>=7.4.4` (34 / 34 passing tests)

---

## 3. Training Configurations

### Supervised Fine-Tuning (`BR-SFT-001-A` Epoch 2.0):
- Base Model: `Qwen/Qwen2.5-14B-Instruct`
- LoRA Rank: $r = 32$, LoRA Alpha: $\alpha = 64$, LoRA Dropout: $0.05$
- Target Modules: `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`
- Precision: `bfloat16`
- Learning Rate: $2.0 \times 10^{-4}$ (Cosine annealing)
- Batch Size: 4 (Gradient Accumulation: 4 $\rightarrow$ Effective Batch Size: 16)
- Epochs: 2.0 (Selected over Epoch 3.0 to prevent behavioral overfitting)

### Direct Preference Optimization (`BR-DPO-002-A`):
- Parent Checkpoint: `outputs/BR-SFT-001-A/checkpoint-epoch-2.0`
- Beta: $\beta = 0.1$
- Learning Rate: $1.0 \times 10^{-5}$
- Precision: `bfloat16`
- Epochs: 1.0 (245 pairs)
- Selected Checkpoint: `checkpoint-100pct`

---

## 4. Unity HPC Infrastructure
- **Workspace**: `/scratch3/workspace/alberto_paz_uri_edu-quahog_neoplasia_analysis/Biomind/`
- **Model Cache (Zero Duplication)**: `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`
- **Slurm Script**: `run_biomind.slurm`
- **Sync Scripts**: `scripts/sync_to_unity.sh`, `scripts/sync_from_unity.sh`

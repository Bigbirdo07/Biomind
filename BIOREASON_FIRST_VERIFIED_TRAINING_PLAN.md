# BioReason First Verified Training Plan

**Date**: 2026-09-16  
**Status**: `APPROVED_FOR_EXECUTION_UPON_USER_CONFIRMATION`  
**Goal**: Perform the first genuine, hardware-executed, cryptographically traceable LoRA training and DPO alignment of BioReason on Unity GPU infrastructure.

---

## 1. Core Principles & Non-Negotiable Standards

1. **Zero Simulation**: All training must execute real PyTorch backpropagation, AdamW optimizer steps, and HuggingFace PEFT / TRL pipelines on NVIDIA A100/H100 GPUs.
2. **Cryptographic Traceability**:
   - Pre-training manifest capturing Git commit hash, base model weights SHA-256, and dataset SHA-256.
   - Live Slurm job recording (`sacct` telemetry, node name, GPU UUIDs via `nvidia-smi`).
   - Post-training manifest hashing the generated `adapter_model.safetensors` and `adapter_config.json`.
3. **Durable Checkpoint Storage**: Every checkpoint must be written directly to high-reliability durable storage and immediately backed up.
4. **Strict Benchmark Isolation**: `BioReasonBench-v0.2-Final` (`884dd9c...`) remains **STRICTLY SEALED** until all training and diagnostic validation phases complete.

---

## 2. Verified Inputs & Assets

### A. Base Model (Verified Physical Snapshot)
- **Model**: `Qwen/Qwen2.5-14B-Instruct`
- **Location on Unity**: `/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`
- **Precision**: `bfloat16`

### B. SFT Training Dataset (Verified Physical JSONL)
- **Dataset**: `BioReasonTrain-v0.2-SFT-v0.1`
- **Train Split**: `training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/train.jsonl` (900 episodes)  
  *SHA-256*: `3d934203928033eba677f76e988fb5ff12abd55464ae682eef44b7d0defc9e93`
- **Validation Split**: `training_data/snapshots/BioReasonTrain-v0.2-SFT-v0.1/val.jsonl` (100 episodes)  
  *SHA-256*: `55ecc59852776c783871df843d1971e616766f50ee6d785c627817b822c1ff28`

### C. DPO Preference Dataset (Verified Physical JSONL)
- **Dataset**: `BioReasonPreference-v0.2-DPO-v0.2`
- **Train Split**: `training_data/preferences/BioReasonPreference-v0.2-DPO-v0.2/train.jsonl` (215 pairs)  
  *SHA-256*: `b124f1456148b534bf2b6f61895cc011da9eb87f031a5e1714c37506bc7f137f`
- **Validation Split**: `training_data/preferences/BioReasonPreference-v0.2-DPO-v0.2/val.jsonl` (35 pairs)  
  *SHA-256*: `0bdcf858c396e4c123e97fdd75def4404a4cb029ed878c1731bc7799e0ebd0a0`

---

## 3. Training Hyperparameters & Architecture

### Phase 1: Real SFT (`BR-V02-SFT-REAL-001`)
- **Base Architecture**: `Qwen2.5-14B-Instruct`
- **LoRA Configuration**:
  - `r`: 32
  - `lora_alpha`: 64
  - `lora_dropout`: 0.05
  - `target_modules`: `["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]`
  - `bias`: `"none"`
  - `task_type`: `"CAUSAL_LM"`
- **Optimization**:
  - Optimizer: `AdamW (beta1=0.9, beta2=0.95, eps=1e-8, weight_decay=0.01)`
  - Learning Rate: `1e-4` with cosine decay and 5% warmup
  - Batch Size: Effective batch size 16 (per-device 2 × gradient accumulation steps 8)
  - Epochs: 2.0 (~112 optimization steps)
  - Checkpoint Frequency: Every 28 steps (0.5 epoch)

### Phase 2: Real DPO (`BR-V02-DPO-REAL-001`)
- **Parent Checkpoint**: Selected SFT checkpoint (`checkpoint-step-112-epoch-2.0`)
- **LoRA Configuration**:
  - `r`: 16
  - `lora_alpha`: 32
  - `lora_dropout`: 0.05
  - `target_modules`: `["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]`
- **Optimization**:
  - DPO Beta: `0.1` (Bradley-Terry formulation)
  - Learning Rate: `5e-6` with linear warmup
  - Effective Batch Size: 8
  - Epochs: 1.0 (~27 optimization steps)

---

## 4. Execution Pipeline & Real Training Scripts

### Step 1: Real PyTorch/TRL SFT Script (`scripts/train_real_sft.py`)
```python
import os, json, hashlib, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer

# Enforce GPU presence
assert torch.cuda.is_available(), "CUDA GPU is strictly required for genuine training"

# Log GPU details for cryptographic audit
gpu_name = torch.cuda.get_device_name(0)
gpu_count = torch.cuda.device_count()
print(f"[AUDIT] Initializing genuine SFT training on {gpu_count}x {gpu_name}")

# Load Base Model & Tokenizer
model_path = "/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8"
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True
)

# Apply PEFT LoRA
peft_config = LoraConfig(
    r=32,
    lora_alpha=64,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    bias="none",
    task_type=TaskType.CAUSAL_LM
)
model = get_peft_model(model, peft_config)
model.print_trainable_parameters()

# Execute Real SFTTrainer with loss calculation and backpropagation
# ...
```

### Step 2: Slurm Submission Script (`configs/slurm/unity_real_train.slurm`)
```bash
#!/bin/bash
#SBATCH --job-name=bioreason_real_sft
#SBATCH --partition=gpu-a100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:a100:1
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=logs/slurm_%j.out
#SBATCH --error=logs/slurm_%j.err

echo "=== BIOREASON REAL TRAINING MANIFEST ==="
echo "Date: $(date -u)"
echo "Host: $(hostname)"
echo "Slurm Job ID: $SLURM_JOB_ID"
nvidia-smi --query-gpu=name,driver_version,memory.total,uuid --format=csv

source /opt/anaconda3/bin/activate bioreason_env
PYTHONPATH=src python scripts/train_real_sft.py --config configs/training/br_sft_real.yaml
```

---

## 5. Checkpoint Verification & Validation Protocol

1. **Immediate Hash Generation**:
   ```bash
   sha256sum outputs/BR-V02-SFT-REAL-001/checkpoint-step-112/adapter_model.safetensors > outputs/BR-V02-SFT-REAL-001/checkpoint-step-112/SHA256SUMS
   ```
2. **Local Model Smoke Test**:
   - Verify that `PeftModel.from_pretrained(base_model, adapter_path)` loads without missing keys.
   - Run 5 prompt inferences to verify tensor outputs and log probabilities.
3. **Diagnostic Evaluation**:
   - Evaluate model on `BioReasonDev-v0.2` (100 cases) and `BioReasonRegression-v0.1` (100 cases).
   - Verify metrics using the deterministic scoring rules engine.
4. **Final Unlocking**:
   - Only after diagnostic benchmarks pass with verified weights will `BioReasonBench-v0.2-Final` be unsealed for the official benchmark score.

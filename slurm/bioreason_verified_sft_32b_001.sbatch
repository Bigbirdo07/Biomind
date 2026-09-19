#!/bin/bash -l
#SBATCH --job-name=br_verified_sft_32b_001
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --constraint=a100-80g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=160G
#SBATCH --time=06:00:00
#SBATCH --output=logs/verified_training/%x_%j.out
#SBATCH --error=logs/verified_training/%x_%j.err
#SBATCH --signal=SIGUSR1@120

set -eo pipefail

export PROJECT_ROOT="${PROJECT_ROOT:-/scratch3/workspace/alberto_paz_uri_edu-quahog_neoplasia_analysis/Biomind}"
export HF_HOME="${HF_HOME:-/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface}"
export QWEN_MODEL_32B="${QWEN_MODEL_32B:-/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-32B-Instruct/snapshots/5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd}"

cd "$PROJECT_ROOT"
mkdir -p logs/verified_training outputs/verified_training/BR-VERIFIED-SFT-32B-001

source ~/miniconda3/etc/profile.d/conda.sh
# Same verified-working base miniconda stack every successful job in this
# project has used (torch 2.13.0+cu130) -- do NOT activate a named env.
export PATH="$HOME/miniconda3/bin:$PATH"

echo "BioReason verified SFT-32B-001 job: $SLURM_JOB_ID"
echo "Hostname: $(hostname)"
echo "CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-UNSET}"
echo "Base model: $QWEN_MODEL_32B"
date
nvidia-smi --query-gpu=name,memory.total --format=csv
python - <<'PY'
import importlib, platform, torch
print("python", platform.python_version())
print("torch", torch.__version__, "cuda", torch.version.cuda, "available", torch.cuda.is_available())
for pkg in ["transformers", "peft", "trl", "accelerate", "bitsandbytes"]:
    try:
        mod = importlib.import_module(pkg)
        print(pkg, getattr(mod, "__version__", "UNKNOWN"))
    except Exception as exc:
        print(pkg, "UNAVAILABLE", repr(exc))
PY

# Same recipe as BR-VERIFIED-SFT-002 (same dataset, same LoRA/lr/epoch
# hyperparameters) -- the ONLY variable changed is the base model
# (14B -> 32B), to isolate whether a bigger base improves outcomes under
# an identical training recipe. See BIOREASON_VERIFIED_SFT_32B_001_REPORT.md
# (to be written after this run) for the resulting comparison against
# BR-VERIFIED-SFT-002 on scripts/live_regression_suite.py.
python scripts/run_verified_sft.py \
  --base-model-path "$QWEN_MODEL_32B" \
  --base-model-name "Qwen/Qwen2.5-32B-Instruct" \
  --run-id "BR-VERIFIED-SFT-32B-001" \
  --output-dir "outputs/verified_training/BR-VERIFIED-SFT-32B-001" \
  --durable-archive-dir "/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-SFT-32B-001" \
  --train-file "training_data/snapshots/BioReasonTrain-Verified-SFT-v0.2/train.jsonl" \
  --val-file "training_data/snapshots/BioReasonTrain-Verified-SFT-v0.2/val.jsonl" \
  --train-format "messages" \
  --assistant-only-label-masking \
  --epochs 2.0 \
  --learning-rate 2e-5 \
  --lora-r 16 \
  --lora-alpha 32

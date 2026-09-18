#!/bin/bash -l
#SBATCH --job-name=br_verified_dpo_002
#SBATCH --partition=uri-gpu
#SBATCH --gres=gpu:1
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
export QWEN_MODEL="${QWEN_MODEL:-/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8}"
export SFT002_ADAPTER="${SFT002_ADAPTER:-/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-SFT-002}"

cd "$PROJECT_ROOT"
mkdir -p logs/verified_training outputs/verified_training/BR-VERIFIED-DPO-002

source ~/miniconda3/etc/profile.d/conda.sh
# NOTE: the named "azera-voice" conda env has an incompatible torch/trl build on some nodes
# (torch 2.5.1+cu121, broken trl FSDPModule import). The base miniconda install has the
# correct, verified-working stack (torch 2.13.0+cu130) that every successful job in this
# project has actually used -- so we deliberately do NOT activate a named env here.
export PATH="$HOME/miniconda3/bin:$PATH"

echo "BioReason verified DPO-002 job: $SLURM_JOB_ID"
echo "Hostname: $(hostname)"
echo "CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-UNSET}"
echo "Base model: $QWEN_MODEL"
echo "Parent adapter (SFT-002): $SFT002_ADAPTER"
date
nvidia-smi
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

# Second verified DPO run. Parent: BR-VERIFIED-SFT-002 (canonical, unchanged).
# Dataset: BioReasonPreference-Verified-DPO-v0.2 (58 pairs, ~3x scale over
# v0.1's 19, following DPO-001's null result). Same conservative
# hyperparameters as DPO-001 (LR 5e-6, beta 0.1) -- this run isolates
# dataset scale as the variable under test, not hyperparameters.
python scripts/run_verified_dpo.py \
  --base-model-path "$QWEN_MODEL" \
  --parent-adapter-path "$SFT002_ADAPTER" \
  --run-id "BR-VERIFIED-DPO-002" \
  --output-dir "outputs/verified_training/BR-VERIFIED-DPO-002" \
  --durable-archive-dir "/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-DPO-002" \
  --train-file "training_data/preferences/BioReasonPreference-Verified-DPO-v0.2/train.jsonl" \
  --val-file "training_data/preferences/BioReasonPreference-Verified-DPO-v0.2/val.jsonl"

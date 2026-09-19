#!/bin/bash -l
#SBATCH --job-name=br_serve_model_32b
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --constraint=a100-80g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=logs/verified_training/%x_%j.out
#SBATCH --error=logs/verified_training/%x_%j.err

set -eo pipefail

export PROJECT_ROOT="${PROJECT_ROOT:-/scratch3/workspace/alberto_paz_uri_edu-quahog_neoplasia_analysis/Biomind}"
export HF_HOME="${HF_HOME:-/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface}"
export QWEN_MODEL_32B="${QWEN_MODEL_32B:-/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-32B-Instruct/snapshots/5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd}"
export SFT32B001_ADAPTER="${SFT32B001_ADAPTER:-/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-SFT-32B-001}"
# Deliberately different port from the 14B server (8099) so both can run
# side-by-side without conflict, and so there is zero chance of the live
# chat product accidentally pointing at the wrong model.
export SERVE_PORT="${SERVE_PORT:-8100}"

cd "$PROJECT_ROOT"
mkdir -p logs/verified_training

source ~/miniconda3/etc/profile.d/conda.sh
export PATH="$HOME/miniconda3/bin:$PATH"

echo "BioReason live model server job (32B): $SLURM_JOB_ID"
echo "Hostname: $(hostname)"
echo "Port: $SERVE_PORT"
echo "Base model: $QWEN_MODEL_32B"
echo "Adapter: $SFT32B001_ADAPTER"
date
nvidia-smi --query-gpu=name,memory.total --format=csv

python scripts/serve_verified_model.py \
  --base-model-path "$QWEN_MODEL_32B" \
  --adapter-path "$SFT32B001_ADAPTER" \
  --port "$SERVE_PORT" \
  --host 0.0.0.0

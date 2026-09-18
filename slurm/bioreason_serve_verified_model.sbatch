#!/bin/bash -l
#SBATCH --job-name=br_serve_model
#SBATCH --partition=uri-gpu
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=logs/verified_training/%x_%j.out
#SBATCH --error=logs/verified_training/%x_%j.err

set -eo pipefail

export PROJECT_ROOT="${PROJECT_ROOT:-/scratch3/workspace/alberto_paz_uri_edu-quahog_neoplasia_analysis/Biomind}"
export HF_HOME="${HF_HOME:-/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface}"
export QWEN_MODEL="${QWEN_MODEL:-/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8}"
export SFT002_ADAPTER="${SFT002_ADAPTER:-/scratch4/workspace/alberto_paz_uri_edu-azera-voice/models/bioreason/verified/BR-VERIFIED-SFT-002}"
export SERVE_PORT="${SERVE_PORT:-8099}"

cd "$PROJECT_ROOT"
mkdir -p logs/verified_training

source ~/miniconda3/etc/profile.d/conda.sh
export PATH="$HOME/miniconda3/bin:$PATH"

echo "BioReason live model server job: $SLURM_JOB_ID"
echo "Hostname: $(hostname)"
echo "Port: $SERVE_PORT"
echo "Base model: $QWEN_MODEL"
echo "Adapter: $SFT002_ADAPTER"
date
nvidia-smi

python scripts/serve_verified_model.py \
  --base-model-path "$QWEN_MODEL" \
  --adapter-path "$SFT002_ADAPTER" \
  --port "$SERVE_PORT" \
  --host 0.0.0.0

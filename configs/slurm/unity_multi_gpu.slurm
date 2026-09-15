#!/bin/bash
#SBATCH --job-name=bioreason_sft_multi_gpu
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --gres=gpu:4
#SBATCH --time=24:00:00
#SBATCH --partition=gpu
#SBATCH --signal=SIGUSR1@120

# ==============================================================================
# BioReason Distributed Multi-GPU Training (FSDP / DeepSpeed / Accelerate)
# ==============================================================================

set -eo pipefail

echo "=========================================================="
echo "Starting BioReason Multi-GPU Job ID: $SLURM_JOB_ID"
echo "Running on Node: $(hostname)"
echo "GPUs: $CUDA_VISIBLE_DEVICES"
echo "Start Time: $(date)"
echo "=========================================================="

mkdir -p logs outputs
export HF_HOME="${HF_HOME:-/tmp/$USER/hf_cache}"
mkdir -p "$HF_HOME"

if [ -d "$HOME/bioreason_venv" ]; then
    source "$HOME/bioreason_venv/bin/activate"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

CONFIG_FILE="${1:-configs/training/lora_sft_p0.yaml}"

# Accelerate distributed launcher
accelerate launch \
    --multi_gpu \
    --num_processes 4 \
    --mixed_precision bf16 \
    scripts/train_sft.py --config "$CONFIG_FILE"

echo "=========================================================="
echo "Multi-GPU Job Completed at: $(date)"
echo "=========================================================="

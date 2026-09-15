#!/bin/bash
#SBATCH --job-name=bioreason_sft_single_gpu
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH --partition=gpu
#SBATCH --signal=SIGUSR1@90

# ==============================================================================
# BioReason SFT Single-GPU Training on UMass Unity HPC
# Handles checkpoint resumption, graceful preemption handling, and clean logging.
# ==============================================================================

set -eo pipefail

echo "=========================================================="
echo "Starting BioReason SFT Job ID: $SLURM_JOB_ID"
echo "Running on Node: $(hostname)"
echo "Allocated GPU: $CUDA_VISIBLE_DEVICES"
echo "Start Time: $(date)"
echo "=========================================================="

# Create log directory
mkdir -p logs outputs

# Trap preemption signal (SIGUSR1) for graceful checkpoint save
checkpoint_handler() {
    echo "[WARNING] Job received SIGUSR1 (preemption/time-limit). Triggering safe checkpoint export..."
    # Training script handles torch checkpointing upon SIGUSR1 / SIGTERM
}
trap 'checkpoint_handler' SIGUSR1

# Activate environment
if [ -d "$HOME/bioreason_venv" ]; then
    source "$HOME/bioreason_venv/bin/activate"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Set Hugging Face cache to scratch space to avoid home quota exhaustion
export HF_HOME="${HF_HOME:-/tmp/$USER/hf_cache}"
mkdir -p "$HF_HOME"

CONFIG_FILE="${1:-configs/training/qlora_sft_p0.yaml}"

python scripts/train_sft.py --config "$CONFIG_FILE"

echo "=========================================================="
echo "BioReason Job Completed Successfully at: $(date)"
echo "=========================================================="

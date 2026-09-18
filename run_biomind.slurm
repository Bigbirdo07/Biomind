#!/bin/bash -l
#SBATCH --job-name=biomind_sft
#SBATCH --partition=uri-gpu
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=logs/biomind_%j.out
#SBATCH --error=logs/biomind_%j.err
#SBATCH --signal=SIGUSR1@90

set -eo pipefail

# 1. Project & Cache Paths
export PROJECT_ROOT="/scratch3/workspace/alberto_paz_uri_edu-quahog_neoplasia_analysis/Biomind"
export HF_HOME="/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface"
export QWEN_MODEL="/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8"

cd "$PROJECT_ROOT"
mkdir -p logs outputs

# 2. Activate Conda Environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate "/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.conda/envs/azera-voice"

# 3. Environment Logging
echo "=========================================================="
echo "Starting Biomind SFT Job ID: $SLURM_JOB_ID"
echo "Running on Node: $(hostname)"
echo "Allocated GPU: $CUDA_VISIBLE_DEVICES"
echo "Model Path: $QWEN_MODEL"
echo "Start Time: $(date)"
echo "=========================================================="

# Trap preemption signal (SIGUSR1) for graceful checkpoint export
checkpoint_handler() {
    echo "[WARNING] Job received SIGUSR1 (preemption/time-limit). Triggering safe checkpoint export..."
}
trap 'checkpoint_handler' SIGUSR1

# 4. Execute Supervised Fine-Tuning
CONFIG_FILE="${1:-configs/training/br_sft_001_a.yaml}"

python3 scripts/train_sft.py --config "$CONFIG_FILE" --model-path "$QWEN_MODEL"

echo "=========================================================="
echo "Biomind SFT Job Completed Successfully at: $(date)"
echo "=========================================================="

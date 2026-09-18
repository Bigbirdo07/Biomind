#!/bin/bash -l
#SBATCH --job-name=br_semantic_rescore_dpo002
#SBATCH --partition=uri-gpu
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=02:00:00
#SBATCH --output=logs/verified_training/%x_%j.out
#SBATCH --error=logs/verified_training/%x_%j.err

set -eo pipefail
export PROJECT_ROOT="${PROJECT_ROOT:-/scratch3/workspace/alberto_paz_uri_edu-quahog_neoplasia_analysis/Biomind}"
export HF_HOME="${HF_HOME:-/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface}"
export QWEN_MODEL="${QWEN_MODEL:-/scratch4/workspace/alberto_paz_uri_edu-azera-voice/.cache/huggingface/hub/models--Qwen--Qwen2.5-14B-Instruct/snapshots/cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8}"
cd "$PROJECT_ROOT"
mkdir -p logs/verified_training outputs/verified_training/semantic_rescore_dpo002
source ~/miniconda3/etc/profile.d/conda.sh
export PATH="$HOME/miniconda3/bin:$PATH"
echo "Semantic rescore DPO-002 job: $SLURM_JOB_ID"; date; nvidia-smi
python scripts/run_semantic_rescore.py \
  --judge-model-path "$QWEN_MODEL" \
  --output-dir "outputs/verified_training/semantic_rescore_dpo002" \
  --only "DPO-002"

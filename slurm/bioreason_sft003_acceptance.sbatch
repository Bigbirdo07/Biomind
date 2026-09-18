#!/bin/bash -l
#SBATCH --job-name=br_sft003_accept
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
export ADAPTER_PATH="${ADAPTER_PATH:-$PROJECT_ROOT/outputs/verified_training/BR-VERIFIED-SFT-003/final_adapter}"
cd "$PROJECT_ROOT"
mkdir -p logs/verified_training outputs/verified_training/BR-VERIFIED-SFT-003/acceptance
source ~/miniconda3/etc/profile.d/conda.sh
# NOTE: the named "azera-voice" conda env has an incompatible torch/trl build on some nodes
# (torch 2.5.1+cu121, broken trl FSDPModule import). The base miniconda install has the
# correct, verified-working stack (torch 2.13.0+cu130) that every successful job in this
# project has actually used -- so we deliberately do NOT activate a named env here.
export PATH="$HOME/miniconda3/bin:$PATH"
echo "SFT-003 acceptance job (same items as SFT-002): $SLURM_JOB_ID"; date; nvidia-smi
python scripts/run_verified_conversation_eval.py \
  --base-model-path "$QWEN_MODEL" \
  --adapter-path "$ADAPTER_PATH" \
  --run-id "SFT-003-LIVE-ACCEPTANCE" \
  --output-dir "outputs/verified_training/BR-VERIFIED-SFT-003/acceptance" \
  --items-file "benchmark/conversation_dev_v0.1/acceptance_items.json" \
  --system-prompt "You are BioReason, a conversational scientific assistant specializing in biology, bioinformatics, experimental design, statistics, and computational biology. Respond naturally to ordinary questions. Use structured scientific audit formats only when they are appropriate or requested. Before building a pipeline, understand the user's experiment and ask for missing consequential information. Do not invent experimental details. Explain computational steps in terms accessible to biological scientists. Identify scientific flaws specifically, not merely by category."

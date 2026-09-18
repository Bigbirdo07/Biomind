#!/bin/bash -l
#SBATCH --job-name=br_check_conda
#SBATCH --partition=uri-gpu
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=logs/verified_training/%x_%j.out
#SBATCH --error=logs/verified_training/%x_%j.err

echo "Hostname: $(hostname)"
export PATH="$HOME/miniconda3/bin:$PATH"
which python3
python3 --version
python3 -c "import torch, trl; print('torch', torch.__version__); print('trl', trl.__version__); from trl import DPOTrainer, DPOConfig; print('DPOTrainer import OK')"

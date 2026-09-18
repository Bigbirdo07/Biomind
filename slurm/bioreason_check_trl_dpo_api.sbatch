#!/bin/bash -l
#SBATCH --job-name=br_check_trl_dpo
#SBATCH --partition=uri-gpu
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:15:00
#SBATCH --output=logs/verified_training/%x_%j.out
#SBATCH --error=logs/verified_training/%x_%j.err

set -eo pipefail
cd /scratch3/workspace/alberto_paz_uri_edu-quahog_neoplasia_analysis/Biomind
source ~/miniconda3/etc/profile.d/conda.sh
# NOTE: the named "azera-voice" conda env has an incompatible torch/trl build on some nodes
# (torch 2.5.1+cu121, broken trl FSDPModule import). The base miniconda install has the
# correct, verified-working stack (torch 2.13.0+cu130) that every successful job in this
# project has actually used -- so we deliberately do NOT activate a named env here.
export PATH="$HOME/miniconda3/bin:$PATH"
python3 -c "
import trl
print('trl', trl.__version__)
from trl import DPOTrainer, DPOConfig
import inspect
print('DPOConfig params:', sorted(inspect.signature(DPOConfig.__init__).parameters.keys()))
print('DPOTrainer params:', sorted(inspect.signature(DPOTrainer.__init__).parameters.keys()))
"

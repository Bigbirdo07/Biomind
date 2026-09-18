#!/bin/bash
# Sync only the code/data needed for verified BioReason Phase T1.
set -euo pipefail

REMOTE_DEST="${REMOTE_DEST:-unity:/scratch3/workspace/alberto_paz_uri_edu-quahog_neoplasia_analysis/Biomind/}"

echo "Syncing verified Phase T1 files to Unity at ${REMOTE_DEST}"
rsync -avz \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='benchmark/final_v0.2' \
  --exclude='human_eval' \
  --exclude='outputs/final_evaluation' \
  ./ "${REMOTE_DEST}"
echo "Verified Phase T1 sync completed."

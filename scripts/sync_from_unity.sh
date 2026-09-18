#!/bin/bash
# Pull trained LoRA checkpoints and run manifests from Unity back to local workspace
set -e

REMOTE_SRC="unity:/scratch3/workspace/alberto_paz_uri_edu-quahog_neoplasia_analysis/Biomind/outputs/"

echo "Pulling outputs from Unity at $REMOTE_SRC to ./outputs/ ..."
mkdir -p ./outputs
rsync -avzP "$REMOTE_SRC" ./outputs/

echo "Pull completed successfully."

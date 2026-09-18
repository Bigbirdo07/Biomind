#!/bin/bash
# Sync local Biomindv2 codebase and training data to UMass Unity scratch workspace
set -e

REMOTE_DEST="unity:/scratch3/workspace/alberto_paz_uri_edu-quahog_neoplasia_analysis/Biomind/"

echo "Syncing local Biomindv2 workspace to Unity at $REMOTE_DEST ..."
rsync -avz --exclude='.git' --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' ./ "$REMOTE_DEST"

echo "Sync completed successfully."

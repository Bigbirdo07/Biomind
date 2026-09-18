#!/bin/bash
# Opens an SSH tunnel from localhost:<port> to the BioReason live model
# server running on a Unity compute node, via the login node (compute nodes
# aren't reachable directly from outside Unity's internal network).
#
# Usage: scripts/tunnel_to_verified_server.sh <compute-node-hostname> [port]
# Example: scripts/tunnel_to_verified_server.sh uri-gpu007 8099
#
# Find <compute-node-hostname> via: ssh unity "squeue -u \$USER -o '%N %j'"
# (look for the br_serve_model job's node).

set -euo pipefail

NODE="${1:?Usage: $0 <compute-node-hostname> [port]}"
PORT="${2:-8099}"

echo "Forwarding localhost:${PORT} -> ${NODE}:${PORT} via unity login node..."
echo "Leave this running; Ctrl+C to stop the tunnel."
ssh -N -L "${PORT}:${NODE}:${PORT}" unity

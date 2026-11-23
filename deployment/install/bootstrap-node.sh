#!/usr/bin/env bash
# Universal Node Bootstrap Script
set -euo pipefail

NODE_ID=${1:-"pi5"}
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

printf '=== Bootstrapping Node: %s ===\n' "$NODE_ID"

SPEC_FILE="$REPO_ROOT/nodes/$NODE_ID/node-spec.yaml"
if [ ! -f "$SPEC_FILE" ]; then
  echo "ERROR: Node specification not found at $SPEC_FILE" >&2
  exit 1
fi

INSTALL_SCRIPT="$REPO_ROOT/nodes/$NODE_ID/install.sh"
if [ -f "$INSTALL_SCRIPT" ]; then
  echo "Running node-specific installer: $INSTALL_SCRIPT"
  bash "$INSTALL_SCRIPT"
else
  echo "Running generic base installer..."
  bash "$REPO_ROOT/nodes/templates/base-install.sh"
fi

echo "✓ Node bootstrap completed for $NODE_ID."

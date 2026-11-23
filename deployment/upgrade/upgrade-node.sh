#!/usr/bin/env bash
# Node Upgrade Script
set -euo pipefail

NODE_ID=${1:-"pi5"}
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

printf '=== Upgrading Node: %s ===\n' "$NODE_ID"

# 1. Create safety backup before upgrading
echo "Creating pre-upgrade configuration backup..."
bash "$REPO_ROOT/deployment/backup/backup-config.sh"

# 2. Update repository if tracked
if [ -d "$REPO_ROOT/.git" ]; then
  echo "Pulling latest infrastructure changes..."
  git -C "$REPO_ROOT" pull --ff-only || echo "Git pull skipped (working tree clean or detached)."
fi

# 3. Re-run node verification
echo "Re-running node verification..."
bash "$REPO_ROOT/nodes/$NODE_ID/verify.sh"

echo "✓ Upgrade and verification completed."

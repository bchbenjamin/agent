#!/usr/bin/env bash
# Tailscale Networking and Verification Helper
set -euo pipefail

printf '=== Tailscale Mesh Verification ===\n'

if ! command -v tailscale >/dev/null 2>&1; then
  echo "Tailscale CLI not found."
  exit 1
fi

status=$(tailscale status || true)
echo "$status"

echo "Checking Tailscale Serve configuration..."
tailscale serve status || echo "No active serve config."
echo "Tailscale verification completed."

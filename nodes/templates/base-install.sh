#!/usr/bin/env bash
# Base installation script for any managed node
set -euo pipefail

printf '=== Personal AI Infrastructure: Base Node Bootstrap ===\n'

# 1. Verify Linux
[ "$(uname -s)" = "Linux" ] || { echo "ERROR: Linux required." >&2; exit 1; }

# 2. Verify non-root execution
[ "$(id -u)" -ne 0 ] || { echo "ERROR: Run as normal user, not root." >&2; exit 1; }

# 3. Check base tools
for tool in curl git python3; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "Installing missing base tool: $tool..."
    sudo apt-get update -qq && sudo apt-get install -y "$tool"
  }
done

echo "✓ Base node dependencies verified."

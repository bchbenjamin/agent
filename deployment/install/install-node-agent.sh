#!/usr/bin/env bash
# Compatibility entry point; the unified installer deploys API, MCP and node agent.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/install-personal-ai.sh"

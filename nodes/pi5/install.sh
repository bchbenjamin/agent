#!/usr/bin/env bash
# Pi 5 Personal AI provisioning entry point. Does not format or repartition storage.
set -euo pipefail
NODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$NODE_DIR/../.." && pwd)"

[ "$(uname -m)" = "aarch64" ] || { echo "Expected aarch64." >&2; exit 1; }
[ "$(id -u)" -ne 0 ] || { echo "Run as bchbenjamin, not root." >&2; exit 1; }
[ "$USER" = "bchbenjamin" ] || { echo "Expected user bchbenjamin." >&2; exit 1; }
bash "$REPO_ROOT/deployment/install/install-personal-ai.sh"

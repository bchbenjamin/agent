#!/usr/bin/env bash
# Pi 5 Personal AI provisioning entry point. Does not format or repartition storage.
set -euo pipefail
NODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$NODE_DIR/../.." && pwd)"

[ "$(uname -m)" = "aarch64" ] || { echo "Expected aarch64." >&2; exit 1; }
[ "$(id -u)" -ne 0 ] || { echo "Run as bchbenjamin, not root." >&2; exit 1; }
[ "$USER" = "bchbenjamin" ] || { echo "Expected user bchbenjamin." >&2; exit 1; }
mountpoint -q /mnt/pi_data || { echo "/mnt/pi_data is not mounted. Refusing to install." >&2; exit 1; }

EXPECTED_UUID="cbdf283b-2951-44de-945e-c082bf87f337"
ACTUAL_UUID="$(findmnt -n -o UUID --target /mnt/pi_data)"
[ "$ACTUAL_UUID" = "$EXPECTED_UUID" ] || {
  echo "Wrong data volume at /mnt/pi_data: expected UUID $EXPECTED_UUID, found $ACTUAL_UUID." >&2
  exit 1
}

bash "$REPO_ROOT/deployment/install/install-personal-ai.sh"

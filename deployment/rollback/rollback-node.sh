#!/usr/bin/env bash
# Node Rollback Script
set -euo pipefail

BACKUP_ARCHIVE=${1:-""}
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ -z "$BACKUP_ARCHIVE" ]; then
  echo "Usage: $0 /path/to/backup-archive.tar.gz" >&2
  exit 1
fi

if [ ! -f "$BACKUP_ARCHIVE" ]; then
  echo "ERROR: Backup archive does not exist: $BACKUP_ARCHIVE" >&2
  exit 1
fi

printf '=== Rolling Back Deployment from: %s ===\n' "$BACKUP_ARCHIVE"
bash "$REPO_ROOT/deployment/backup/restore.sh" "$BACKUP_ARCHIVE"
echo "✓ Rollback completed."

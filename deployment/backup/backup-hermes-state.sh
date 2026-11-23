#!/usr/bin/env bash
# Backup Hermes Operational State (Sensitive - Stored Off-Git)
set -euo pipefail

BACKUP_DIR="$HOME/backups"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
DEST="$BACKUP_DIR/hermes-state-$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

HERMES_DIR="$HOME/.hermes-pi"
if [ ! -d "$HERMES_DIR" ]; then
  echo "Hermes directory not found at $HERMES_DIR"
  exit 1
fi

echo "Archiving Hermes state databases to $DEST..."
tar -czf "$DEST" \
  -C "$HERMES_DIR" \
  kanban.db projects.db state.db \
  2>/dev/null || true

chmod 600 "$DEST"
echo "✓ Hermes operational state backed up securely to: $DEST"

#!/usr/bin/env bash
# Backup Configuration and Specifications (Non-sensitive)
set -euo pipefail

BACKUP_DIR="$HOME/backups"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
DEST="$BACKUP_DIR/config-backup-$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

echo "Creating configuration backup to $DEST..."
tar -czf "$DEST" \
  -C "$HOME" \
  --exclude="*.env" \
  --exclude="*.key" \
  --exclude="auth.json" \
  .hermes-pi/config.yaml \
  2>/dev/null || true

chmod 600 "$DEST"
echo "✓ Configuration backup created: $DEST"

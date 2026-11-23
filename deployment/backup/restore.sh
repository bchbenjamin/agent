#!/usr/bin/env bash
# Restoration Script from Backup Archive
set -euo pipefail

ARCHIVE=${1:-""}
TARGET_DIR=${2:-"$HOME"}

if [ -z "$ARCHIVE" ] || [ ! -f "$ARCHIVE" ]; then
  echo "Usage: $0 /path/to/archive.tar.gz [target_dir]" >&2
  exit 1
fi

printf 'Restoring from %s to %s...\n' "$ARCHIVE" "$TARGET_DIR"
tar -xzf "$ARCHIVE" -C "$TARGET_DIR"
echo "✓ Restoration completed."

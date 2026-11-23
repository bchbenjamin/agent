#!/usr/bin/env bash
# Bootstrap Script for Redmi Note 5 Pro Linux Node
set -euo pipefail

printf '=== Personal AI Infrastructure: Redmi Note 5 Pro Bootstrap ===\n'
echo "Checking environment..."

ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ]; then
  echo "WARNING: Running on $ARCH. Target is Snapdragon 636 (aarch64)."
fi

# Detect whether running inside Termux / PRoot or Native Linux
if [ -d "/data/data/com.termux" ]; then
  echo "Detected Termux environment. Installing PRoot Linux container..."
  pkg update -y && pkg install -y proot-distro git curl
  proot-distro install debian || true
  echo "Debian container provisioned in proot."
else
  echo "Standard Linux environment detected. Verifying Node Agent dependencies..."
  command -v python3 >/dev/null 2>&1 || sudo apt-get install -y python3
fi

echo "✓ Redmi bootstrap prerequisites staged."

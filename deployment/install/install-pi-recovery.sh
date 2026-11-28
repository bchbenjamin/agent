#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OWNER=bchbenjamin
APP_DIR="/home/$OWNER/Applications"

if [[ "$(id -un)" != "$OWNER" || "$(id -u)" -eq 0 ]]; then
  echo "Run as $OWNER from the repository checkout; this script uses sudo." >&2
  exit 2
fi

# This repair is intentionally independent of /mnt/pi_data, so it can install
# the service-recovery timer while the SSD is unavailable. It never mounts,
# fscks, or modifies the contents of a block device itself.
sudo install -o root -g root -m 0755 "$REPO_ROOT/deployment/recovery/personal-ai-storage-recovery.py" /usr/local/libexec/personal-ai-storage-recovery.py
sudo install -o root -g root -m 0644 "$REPO_ROOT/deployment/systemd/personal-ai-storage-recovery.service" /etc/systemd/system/personal-ai-storage-recovery.service
sudo install -o root -g root -m 0644 "$REPO_ROOT/deployment/systemd/personal-ai-storage-recovery.timer" /etc/systemd/system/personal-ai-storage-recovery.timer
sudo systemctl daemon-reload

APPIMAGE="$(find "$APP_DIR" -maxdepth 1 -type f -name 'Beeper-*-arm64.AppImage' -printf '%f\n' | sort -V | tail -1)"
if [[ -n "$APPIMAGE" && -x "$APP_DIR/$APPIMAGE" ]]; then
  TMP_LINK="$APP_DIR/.Beeper.AppImage.$$.tmp"
  trap 'rm -f "$TMP_LINK"' EXIT
  ln -s "$APPIMAGE" "$TMP_LINK"
  mv -Tf "$TMP_LINK" "$APP_DIR/Beeper.AppImage"
  sudo install -o root -g root -m 0644 "$REPO_ROOT/deployment/systemd/beeper.service" /etc/systemd/system/beeper.service
  sudo systemctl daemon-reload
  sudo systemctl enable beeper.service
  sudo systemctl reset-failed beeper.service
  echo "Beeper stable path set to installed $APPIMAGE; no existing process was stopped or started."
else
  echo "No executable Beeper ARM64 AppImage found; storage recovery will still be installed."
fi

sudo systemctl enable --now personal-ai-storage-recovery.timer
echo "Installed and enabled API/MCP recovery timer. It starts services only after fstab has mounted the expected UUID and API health succeeds; it never mounts or fscks the SSD."

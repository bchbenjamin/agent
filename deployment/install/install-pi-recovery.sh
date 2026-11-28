#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OWNER=bchbenjamin
APP_DIR="/home/$OWNER/Applications"

if [[ "$(id -un)" != "$OWNER" || "$(id -u)" -eq 0 ]]; then
  echo "Run as $OWNER from the repository checkout; this script uses sudo." >&2
  exit 2
fi

# This repair is independent of optional bulk storage. It updates the stable
# Beeper path and graphical-session unit without starting a duplicate process.
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
  echo "No executable Beeper ARM64 AppImage found; existing application data was left untouched."
fi

echo "Installed graphical-session-aware Beeper recovery; core Personal AI state is microSD-backed."

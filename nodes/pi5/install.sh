#!/usr/bin/env bash
# Idempotent Node Provisioning Script for Raspberry Pi 5
set -euo pipefail

NODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$NODE_DIR/../.." && pwd)"

printf '=== Personal AI Infrastructure: Pi 5 Provisioning ===\n'

# 1. Architecture check
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ]; then
  echo "ERROR: Expected aarch64, got $ARCH" >&2
  exit 1
fi

# 2. Check user
if [ "$(id -u)" -eq 0 ]; then
  echo "ERROR: Run as normal user (e.g. bchbenjamin), not root." >&2
  exit 1
fi

# 3. Prerequisites check
for pkg in curl git python3 openssl xdotool wtype tesseract-ocr at-spi2-core; do
  if ! dpkg -s "$pkg" >/dev/null 2>&1 && ! command -v "$pkg" >/dev/null 2>&1; then
    echo "Installing missing package: $pkg..."
    sudo apt-get update -qq && sudo apt-get install -y "$pkg"
  fi
done

# 4. Storage mount verification (/mnt/pi_data)
if ! grep -qs '/mnt/pi_data' /proc/mounts; then
  echo "Mounting /mnt/pi_data..."
  sudo mkdir -p /mnt/pi_data
  sudo mount -a || true
fi

# 5. Uinput permissions
if [ ! -f /etc/udev/rules.d/99-uinput.rules ]; then
  echo "Configuring uinput rules..."
  echo 'KERNEL=="uinput", SUBSYSTEM=="misc", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-uinput.rules >/dev/null
  sudo udevadm control --reload-rules && sudo udevadm trigger
fi
if ! groups "$USER" | grep -qw "input"; then
  echo "Adding $USER to input group..."
  sudo usermod -aG input "$USER"
fi

# 6. Computer Use Linux installation
if ! command -v computer-use-linux >/dev/null 2>&1; then
  echo "computer-use-linux not found in PATH. Check /usr/local/bin/."
else
  echo "computer-use-linux present: $(computer-use-linux --version)"
fi

# 7. Beeper Systemd Service verification
if [ -f /etc/systemd/system/beeper.service ]; then
  if ! systemctl is-enabled beeper.service >/dev/null 2>&1; then
    sudo systemctl enable beeper.service
  fi
  if ! systemctl is-active beeper.service >/dev/null 2>&1; then
    sudo systemctl start beeper.service
  fi
fi

# 8. Hermes Gateway User Service verification
HERMES_HOME=${HERMES_HOME:-"$HOME/.hermes-pi"}
export HERMES_HOME
if command -v hermes >/dev/null 2>&1; then
  sudo loginctl enable-linger "$USER" || true
  if ! systemctl --user is-active hermes-gateway-*.service >/dev/null 2>&1; then
    hermes gateway install --start-now --start-on-login || true
  fi
fi

printf '\n✓ Pi 5 node provisioning verification completed successfully.\n'

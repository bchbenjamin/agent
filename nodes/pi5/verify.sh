#!/usr/bin/env bash
# Verification Suite for Raspberry Pi 5 Managed Node
set -euo pipefail

HERMES_HOME=${HERMES_HOME:-"$HOME/.hermes-pi"}
export HERMES_HOME

printf '=== Verifying Node: Raspberry Pi 5 ===\n\n'

# 1. System Services
printf '1. Checking System Services:\n'
for svc in beeper.service lightdm.service wayvnc.service tailscaled.service; do
  status=$(systemctl is-active "$svc" 2>/dev/null || echo "inactive")
  printf '  - %-22s : %s\n' "$svc" "$status"
  [ "$status" = "active" ] || echo "    WARNING: $svc is not active"
done

# 2. User Services
printf '\n2. Checking User Services:\n'
for svc in at-spi-dbus-bus.service; do
  status=$(systemctl --user is-active "$svc" 2>/dev/null || echo "inactive")
  printf '  - %-22s : %s\n' "$svc" "$status"
done

# 3. Hermes Gateway & Local API
printf '\n3. Checking Hermes Gateway:\n'
if command -v hermes >/dev/null 2>&1; then
  hermes gateway status || echo "Gateway status check completed."
  api_health=$(curl -fsS --max-time 5 http://127.0.0.1:8642/health 2>/dev/null || echo "UNAVAILABLE")
  printf '  - Local API (8642)     : %s\n' "$api_health"
else
  echo '  - Hermes CLI not installed'
fi

# 4. Beeper Local API
printf '\n4. Checking Beeper Local API:\n'
beeper_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:23373/v0/mcp || echo "000")
printf '  - Beeper API (23373)   : HTTP %s\n' "$beeper_status"

# 5. Storage
printf '\n5. Checking Storage Mounts:\n'
if grep -qs '/mnt/pi_data' /proc/mounts; then
  avail=$(df -h /mnt/pi_data | awk 'NR==2 {print $4}')
  printf '  - /mnt/pi_data (SSD)   : Mounted (%s available)\n' "$avail"
else
  printf '  - /mnt/pi_data (SSD)   : NOT MOUNTED\n'
fi

# 6. Computer-Use Linux Doctor
printf '\n6. Checking Computer-Use Linux:\n'
if command -v computer-use-linux >/dev/null 2>&1; then
  export WAYLAND_DISPLAY="wayland-0"
  export DISPLAY=":0"
  export XDG_RUNTIME_DIR="/run/user/1000"
  doc_out=$(computer-use-linux doctor 2>/dev/null || echo '{"readiness":{"blockers":["Failed to run"]}}')
  blockers=$(echo "$doc_out" | grep -o '"blockers":\s*\[[^]]*\]' || echo '"blockers": []')
  printf '  - Diagnostics          : %s\n' "$blockers"
fi

printf '\n=== Node Verification Complete ===\n'

#!/usr/bin/env bash
# Read-only health checks for the Pi 5 Personal AI node.
set -u
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes-pi}"
printf '=== Raspberry Pi 5 / Personal AI Verification ===\n'

check_service() {
  local unit="$1" state enabled
  state="$(systemctl is-active "$unit" 2>/dev/null || true)"
  enabled="$(systemctl is-enabled "$unit" 2>/dev/null || true)"
  printf '  %-30s active=%-10s enabled=%s\n' "$unit" "${state:-unknown}" "${enabled:-unknown}"
}

echo '1. Core system services'
for svc in beeper.service lightdm.service wayvnc.service tailscaled.service; do check_service "$svc"; done

echo '\n2. Personal AI services'
for svc in personal-ai-api.service personal-ai-mcp.service personal-ai-node.service; do check_service "$svc"; done
printf "  %-30s %s\n" personal-ai-storage-recovery.timer "legacy; not required"

echo '\n3. API health'
curl -fsS --max-time 5 http://127.0.0.1:8000/health || echo '  Personal AI API unavailable'

echo '\n4. MCP authentication boundary (401 expected without a token)'
code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:8765/mcp || echo 000)"
printf '  MCP unauthenticated status: HTTP %s\n' "$code"
[ "$code" = 401 ] || echo '  WARNING: MCP should reject requests without a bearer token.'

echo '\n5. Node agent identity'
if systemctl is-active --quiet personal-ai-node.service; then
  pid="$(systemctl show -p MainPID --value personal-ai-node.service)"
  if [ "$pid" -gt 0 ] 2>/dev/null; then
    ps -o user=,pid=,args= -p "$pid"
  fi
else
  echo '  Node agent not active'
fi

echo '\n6. Hermes local API'
curl -fsS --max-time 5 http://127.0.0.1:8642/health || echo '  Hermes API unavailable'

echo '\n7. Beeper local MCP endpoint'
beeper_code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:23373/v0/mcp || echo 000)"
printf '  Beeper endpoint: HTTP %s (401 is expected before OAuth)\n' "$beeper_code"

echo '\n8. Essential state on microSD'
if mountpoint -q /mnt/pi_data; then
  actual_uuid="$(findmnt -n -o UUID --target /mnt/pi_data 2>/dev/null || true)"
  expected_uuid="cbdf283b-2951-44de-945e-c082bf87f337"
  printf '  UUID: %s (expected %s)\n' "${actual_uuid:-unknown}" "$expected_uuid"
  [ "$actual_uuid" = "$expected_uuid" ] || echo '  WARNING: mounted data volume UUID does not match the Pi SSD.'
  df -h /mnt/pi_data | tail -1
  echo '  Optional SSD mounted; core services must not depend on it.'
else
  echo '  Optional SSD absent; this must not block core services.'
fi

if [ -f /var/lib/pai-api/control-plane.sqlite3 ]; then
  stat -c '  Control-plane DB on boot volume: %U:%G %a, %s bytes' /var/lib/pai-api/control-plane.sqlite3
else
  echo '  Control-plane DB missing at /var/lib/pai-api/control-plane.sqlite3'
fi

echo '\n9. Hermes user services'
systemctl --user is-active hermes-gateway-e86e8d0b.service 2>/dev/null || true
systemctl --user is-active at-spi-dbus-bus.service 2>/dev/null || true

echo '\n10. Computer Use'
if command -v hermes >/dev/null 2>&1; then
  HERMES_HOME="$HERMES_HOME" hermes computer-use doctor 2>&1 | tail -30 || true
else
  echo '  Hermes CLI not installed'
fi

echo '\n=== Verification checks complete; review all warnings above. ==='

#!/usr/bin/env bash
# First deployment of the Personal AI control plane, MCP adapter and Pi node agent.
# Run as bchbenjamin from a clean checkout after verifying /mnt/pi_data.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET=/opt/personal-ai
USER_NAME="bchbenjamin"
GROUP_NAME="$(id -gn "$USER_NAME")"
NODE_AGENT_USER="pai-agent"
API_ENV=/etc/personal-ai/api.env
NODE_ENV=/etc/personal-ai/node.env
MCP_ENV=/etc/personal-ai/mcp.env
API_USER="pai-api"
MCP_USER="pai-mcp"
ADMIN_TOKEN_FILE=/etc/personal-ai/admin-token

if [ "$(id -u)" -eq 0 ] || [ "$USER" != "$USER_NAME" ]; then
  echo "Run as the unprivileged $USER_NAME account with sudo access." >&2
  exit 1
fi
[ "$(uname -m)" = "aarch64" ] || { echo "Expected ARM64/aarch64." >&2; exit 1; }
mountpoint -q /mnt/pi_data || { echo "/mnt/pi_data must be mounted; refusing to put state on the boot card." >&2; exit 1; }
EXPECTED_DATA_UUID="cbdf283b-2951-44de-945e-c082bf87f337"
ACTUAL_DATA_UUID="$(findmnt -n -o UUID --target /mnt/pi_data)"
[ "$ACTUAL_DATA_UUID" = "$EXPECTED_DATA_UUID" ] || {
  echo "Wrong data volume at /mnt/pi_data: expected UUID $EXPECTED_DATA_UUID, found $ACTUAL_DATA_UUID." >&2
  exit 1
}

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip curl sudo git
if [ -L "$TARGET" ] || { [ -e "$TARGET" ] && [ "$(stat -c %u "$TARGET")" != 0 ]; }; then
  echo "Review and relocate the existing non-root-owned installation at $TARGET before deploying." >&2
  exit 1
fi
sudo install -d -o root -g root -m 0755 "$TARGET"
git -C "$REPO_ROOT" archive HEAD | sudo tar --no-same-owner -xf - -C "$TARGET"
sudo python3 -m venv "$TARGET/.venv"
sudo "$TARGET/.venv/bin/python" -m pip install -r "$TARGET/requirements.txt"

sudo install -d -o "$USER_NAME" -g "$GROUP_NAME" -m 0700 "/home/$USER_NAME/.config/personal-ai"
for service_user in "$API_USER" "$MCP_USER" "$NODE_AGENT_USER"; do
  if ! id "$service_user" >/dev/null 2>&1; then
    sudo useradd --system --user-group --home-dir "/var/lib/$service_user" --create-home --shell /usr/sbin/nologin "$service_user"
  fi
done
sudo install -d -o "$API_USER" -g "$API_USER" -m 0700 /mnt/pi_data/personal-ai /var/lib/pai-api
sudo chown -R "$API_USER:$API_USER" /mnt/pi_data/personal-ai
sudo chmod 0700 /mnt/pi_data/personal-ai
sudo install -d -o "$MCP_USER" -g "$MCP_USER" -m 0700 /var/lib/pai-mcp
sudo install -d -o "$NODE_AGENT_USER" -g "$NODE_AGENT_USER" -m 0700 /var/lib/pai-agent /var/lib/pai-agent/pending-results
sudo install -d -o root -g root -m 0755 /etc/personal-ai /usr/local/libexec

# Generate first-run credentials once. They are never committed to the repository.
NEW_ADMIN=0
if ! sudo test -f "$API_ENV"; then
  BOOTSTRAP_TOKEN="$("$TARGET/.venv/bin/python" -c 'import secrets; print("pai_admin_"+secrets.token_urlsafe(40))')"
  ENROLL_TOKEN="$("$TARGET/.venv/bin/python" -c 'import secrets; print(secrets.token_urlsafe(40))')"
  TMP_ENV="$(mktemp)"
  umask 077
  cat > "$TMP_ENV" <<EOF
PAI_DB_PATH=/mnt/pi_data/personal-ai/pai.sqlite3
PAI_BOOTSTRAP_TOKEN=$BOOTSTRAP_TOKEN
PAI_NODE_ENROLLMENT_TOKEN=$ENROLL_TOKEN
EOF
  sudo install -o root -g "$API_USER" -m 0640 "$TMP_ENV" "$API_ENV"
  rm -f "$TMP_ENV"
  TMP_ADMIN="$(mktemp)"
  printf '%s\n' "$BOOTSTRAP_TOKEN" > "$TMP_ADMIN"
  sudo install -o root -g root -m 0600 "$TMP_ADMIN" "$ADMIN_TOKEN_FILE"
  rm -f "$TMP_ADMIN"
  NEW_ADMIN=1
else
  BOOTSTRAP_TOKEN="$(sudo sed -n 's/^PAI_BOOTSTRAP_TOKEN=//p' "$API_ENV" | head -1)"
  ENROLL_TOKEN="$(sudo sed -n 's/^PAI_NODE_ENROLLMENT_TOKEN=//p' "$API_ENV" | head -1)"
  if [ -n "$BOOTSTRAP_TOKEN" ] && ! sudo test -f "$ADMIN_TOKEN_FILE"; then
    TMP_ADMIN="$(mktemp)"
    printf '%s\n' "$BOOTSTRAP_TOKEN" > "$TMP_ADMIN"
    sudo install -o root -g root -m 0600 "$TMP_ADMIN" "$ADMIN_TOKEN_FILE"
    rm -f "$TMP_ADMIN"
  fi
fi
sudo chown root:"$API_USER" "$API_ENV"
sudo chmod 0640 "$API_ENV"

sudo tee "$NODE_ENV" >/dev/null <<EOF
PAI_API_URL=http://127.0.0.1:8000
PAI_NODE_ID=pi5
PAI_TAILSCALE_IP=$(tailscale ip -4 2>/dev/null | head -1 || true)
PAI_NODE_TOKEN_FILE=/var/lib/pai-agent/node-token
PAI_NODE_PENDING_DIR=/var/lib/pai-agent/pending-results
EOF
sudo chown root:"$NODE_AGENT_USER" "$NODE_ENV"
sudo chmod 0640 "$NODE_ENV"

# Migrate a token created by an earlier prototype into the isolated pai-agent account.
OLD_TOKEN="/home/$USER_NAME/.config/personal-ai/node-token"
if ! sudo -u "$NODE_AGENT_USER" test -s /var/lib/pai-agent/node-token && [ -s "$OLD_TOKEN" ]; then
  sudo install -o "$NODE_AGENT_USER" -g "$NODE_AGENT_USER" -m 0600 "$OLD_TOKEN" /var/lib/pai-agent/node-token
  rm -f "$OLD_TOKEN"
fi
if ! sudo test -f "$MCP_ENV"; then
  sudo tee "$MCP_ENV" >/dev/null <<'EOF'
PAI_API_URL=http://127.0.0.1:8000
EOF
fi
sudo chown root:"$MCP_USER" "$MCP_ENV"
sudo chmod 0640 "$MCP_ENV"

sudo install -o root -g root -m 0755 "$TARGET/deployment/privileged/pai-privileged" /usr/local/libexec/pai-privileged
sudo install -o root -g root -m 0440 "$TARGET/deployment/privileged/pai-node-agent.sudoers" /etc/sudoers.d/pai-node-agent
sudo visudo -cf /etc/sudoers.d/pai-node-agent

for unit in personal-ai-api.service personal-ai-mcp.service personal-ai-node.service; do
  sudo install -o root -g root -m 0644 "$TARGET/deployment/systemd/$unit" "/etc/systemd/system/$unit"
done
sudo systemctl daemon-reload
sudo systemctl enable personal-ai-api.service personal-ai-mcp.service personal-ai-node.service
sudo systemctl restart personal-ai-api.service

for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null; then break; fi
  sleep 1
done
curl -fsS http://127.0.0.1:8000/health >/dev/null || {
  sudo journalctl -u personal-ai-api.service -n 80 --no-pager
  exit 1
}

TOKEN_FILE=/var/lib/pai-agent/node-token
if ! sudo -u "$NODE_AGENT_USER" test -s "$TOKEN_FILE"; then
  [ -n "${ENROLL_TOKEN:-}" ] || { echo "Missing PAI_NODE_ENROLLMENT_TOKEN in $API_ENV." >&2; exit 2; }
  printf '%s\n' "$ENROLL_TOKEN" | (
    cd "$TARGET"
    sudo -u "$NODE_AGENT_USER" env PAI_API_URL=http://127.0.0.1:8000 PAI_NODE_ID=pi5 \
      PAI_NODE_TOKEN_FILE="$TOKEN_FILE" /bin/bash -c '
        IFS= read -r PAI_NODE_ENROLLMENT_TOKEN || exit 1
        export PAI_NODE_ENROLLMENT_TOKEN
        exec "$1" -m node_agent.cli --enroll
      ' bash "$TARGET/.venv/bin/python"
  )
fi

# Remove one-time bootstrap/enrollment secrets from the API service environment.
# Their hashes/credentials are already persisted; retaining these env values would
# re-enable bootstrap or allow additional node enrollment after every restart.
if sudo grep -q '^PAI_BOOTSTRAP_TOKEN=' "$API_ENV" || sudo grep -q '^PAI_NODE_ENROLLMENT_TOKEN=' "$API_ENV"; then
  sudo sed -i '/^PAI_BOOTSTRAP_TOKEN=/d; /^PAI_NODE_ENROLLMENT_TOKEN=/d' "$API_ENV"
  sudo systemctl restart personal-ai-api.service
  for i in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then break; fi
    sleep 1
  done
fi

sudo systemctl restart personal-ai-node.service
sudo systemctl restart personal-ai-mcp.service

echo "Personal AI API, MCP adapter and Pi node agent are installed."
echo "API health: $(curl -fsS http://127.0.0.1:8000/health)"
echo "MCP listener: 127.0.0.1:8765/mcp (requires an API-issued Bearer token)"
echo "Node status: $(sudo systemctl is-active personal-ai-node.service)"
if [ "$NEW_ADMIN" -eq 1 ]; then
  echo
  echo "Initial admin bearer token saved root-only at $ADMIN_TOKEN_FILE."
  echo "Issue client credentials as pai-api with: sudo -u pai-api env PAI_DB_PATH=/mnt/pi_data/personal-ai/pai.sqlite3 $TARGET/.venv/bin/python -m personal_ai_api.cli issue-token ..."
fi

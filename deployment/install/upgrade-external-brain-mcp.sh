#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

# In-place upgrade only. This does not run first-install provisioning and does
# not replace the existing service units, virtual environment, DB, or API keys.
if [[ ${EUID} -ne 0 ]]; then
  echo "Run this script with sudo from the synchronized repository." >&2
  exit 2
fi

REPO="$(git -C "$(dirname "${BASH_SOURCE[0]}")/../.." rev-parse --show-toplevel)"
INSTALL=/opt/personal-ai
DB=/mnt/pi_data/personal-ai/pai.sqlite3
OWNER=bchbenjamin
OWNER_HOME="$(getent passwd "$OWNER" | cut -d: -f6)"
MCP_ENV=/etc/personal-ai/mcp.env
TOKEN_DIR="$OWNER_HOME/.config/personal-ai/external-brain"
TOKEN_FILE="$TOKEN_DIR/claude.token"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/mnt/pi_data/personal-ai-upgrade-${STAMP}"

git -C "$REPO" merge-base --is-ancestor f285d3d HEAD || {
  echo "Repository does not contain required external-brain security commit f285d3d." >&2
  exit 2
}
mountpoint -q /mnt/pi_data || { echo "/mnt/pi_data is not mounted; refusing deployment." >&2; exit 2; }
[[ -f "$DB" && -d "$INSTALL/.venv" && -f "$MCP_ENV" ]] || {
  echo "Expected installed API database, venv, or MCP environment is missing." >&2
  exit 2
}
systemctl is-active --quiet personal-ai-api.service
systemctl is-active --quiet personal-ai-mcp.service
if [[ -e "$TOKEN_FILE" ]]; then
  echo "Refusing to overwrite existing external-brain token file: $TOKEN_FILE" >&2
  echo "Use the existing credential or revoke its client explicitly before choosing a new file." >&2
  exit 2
fi

install -d -o root -g root -m 0700 "$BACKUP"
python3 - "$DB" "$BACKUP/pai.sqlite3" <<'PY'
import os, sqlite3, sys
source, destination = sys.argv[1:]
src = sqlite3.connect(f"file:{source}?mode=ro", uri=True, timeout=15)
dst = sqlite3.connect(destination, timeout=15)
try:
    src.backup(dst)
    result = dst.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise SystemExit(f"SQLite backup integrity failed: {result}")
finally:
    dst.close()
    src.close()
os.chmod(destination, 0o600)
PY

tar -czf "$BACKUP/installed-source.tar.gz" -C "$INSTALL" control_plane personal_ai_api pai_mcp
chmod 0600 "$BACKUP/installed-source.tar.gz"

# Copy only reviewed source files needed by the external-brain release. The
# installed virtual environment and all service configuration remain in place.
install -D -o root -g root -m 0644 "$REPO/control-plane/authorization/scopes.py" "$INSTALL/control_plane/authorization/scopes.py"
install -D -o root -g root -m 0644 "$REPO/control-plane/storage.py" "$INSTALL/control_plane/storage.py"
install -D -o root -g root -m 0644 "$REPO/personal-ai-api/routes/context.py" "$INSTALL/personal_ai_api/routes/context.py"
install -D -o root -g root -m 0644 "$REPO/personal-ai-api/routes/tasks.py" "$INSTALL/personal_ai_api/routes/tasks.py"
install -D -o root -g root -m 0644 "$REPO/pai_mcp/adapter.py" "$INSTALL/pai_mcp/adapter.py"
install -D -o root -g root -m 0644 "$REPO/pai_mcp/instructions.py" "$INSTALL/pai_mcp/instructions.py"
install -D -o root -g root -m 0644 "$REPO/pai_mcp/integrations.py" "$INSTALL/pai_mcp/integrations.py"
install -D -o root -g root -m 0644 "$REPO/pai_mcp/hermes_sessions.py" "$INSTALL/pai_mcp/hermes_sessions.py"
install -D -o root -g root -m 0644 "$REPO/pai_mcp/server.py" "$INSTALL/pai_mcp/server.py"

# Reuse authorized Box and Beeper credentials from Hermes without displaying
# them. Preserve every unrelated line already present in the MCP environment.
python3 - "$OWNER_HOME" "$MCP_ENV" <<'PY'
import datetime, json, os, pwd, re, sys, tempfile
from pathlib import Path

home, target = map(Path, sys.argv[1:])
env_file = home / ".hermes-pi/.env"
values = {}
for raw in env_file.read_text().splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    line = line.removeprefix("export ")
    if "=" in line:
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")

updates = {}
box = values.get("MCP_BOX_API_KEY", "")
if box:
    updates["PAI_BOX_MCP_TOKEN"] = box
hermes_key = values.get("API_SERVER_KEY", "")
if hermes_key:
    updates["PAI_HERMES_API_KEY"] = hermes_key

beeper_file = home / ".hermes-pi/mcp-tokens/beeper.json"
if beeper_file.is_file():
    data = json.loads(beeper_file.read_text())
    token = data.get("access_token", "")
    expiry = data.get("expires_at")
    valid = bool(token)
    if isinstance(expiry, (int, float)):
        valid = valid and expiry > datetime.datetime.now().timestamp()
    elif isinstance(expiry, str):
        try:
            parsed = datetime.datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=datetime.timezone.utc)
            valid = valid and parsed.timestamp() > datetime.datetime.now().timestamp()
        except ValueError:
            valid = False
    if valid:
        updates["PAI_BEEPER_MCP_TOKEN"] = token

for key, value in updates.items():
    if not re.fullmatch(r"[A-Za-z0-9._~+/=-]+", value):
        raise SystemExit(f"Existing {key} credential has unsupported characters; refusing to rewrite env file.")

lines = target.read_text().splitlines()
for key, value in updates.items():
    replacement = f"{key}={value}"
    found = False
    for i, line in enumerate(lines):
        if line.split("=", 1)[0].strip() == key:
            lines[i] = replacement
            found = True
            break
    if not found:
        lines.append(replacement)
fd, staging = tempfile.mkstemp(prefix=".mcp.env.", dir=str(target.parent))
try:
    with os.fdopen(fd, "w") as output:
        output.write("\n".join(lines) + "\n")
        output.flush()
        os.fsync(output.fileno())
    os.chmod(staging, 0o640)
    os.chown(staging, 0, pwd.getgrnam("pai-mcp").gr_gid)
    os.replace(staging, target)
finally:
    if os.path.exists(staging):
        os.unlink(staging)
print("Configured existing integration credentials:", ", ".join(sorted(updates)) if updates else "none; prior environment preserved")
PY

"$INSTALL/.venv/bin/python" -m compileall -q "$INSTALL/control_plane" "$INSTALL/personal_ai_api" "$INSTALL/pai_mcp"
systemctl restart personal-ai-api.service
systemctl restart personal-ai-mcp.service
systemctl is-active --quiet personal-ai-api.service
systemctl is-active --quiet personal-ai-mcp.service

# Issue a separate restricted external-brain credential without sending it to
# stdout or modifying Hermes's existing Personal AI token.
install -d -o "$OWNER" -g "$OWNER" -m 0700 "$TOKEN_DIR"
CLIENT_ID="claude-external-${STAMP}"
TOKEN="$(runuser -u pai-api -- env PAI_DB_PATH="$DB" PYTHONPATH="$INSTALL" \
  "$INSTALL/.venv/bin/python" -m personal_ai_api.cli issue-token \
  --client-id "$CLIENT_ID" --client-type external-brain \
  --scopes context:read,context:write,nodes:read,terminal:execute,box:read,box:execute,beeper:read,sessions:read)"
[[ "$TOKEN" == pai_external-brain_* ]] || { echo "Token issuance failed; see CLI status." >&2; exit 4; }
umask 077
printf '%s\n' "$TOKEN" > "$TOKEN_FILE"
chown "$OWNER:$OWNER" "$TOKEN_FILE"
chmod 0600 "$TOKEN_FILE"
unset TOKEN

echo "External-brain MCP upgrade installed."
echo "Database and source backups: $BACKUP"
echo "Restricted Claude token file: $TOKEN_FILE (value not displayed)"
echo "Services: personal-ai-api=$(systemctl is-active personal-ai-api.service), personal-ai-mcp=$(systemctl is-active personal-ai-mcp.service)"
echo "The node agent was not restarted."

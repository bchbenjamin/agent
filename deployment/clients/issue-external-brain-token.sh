#!/usr/bin/env bash
# Owner-run credential provisioning only. Never print the bearer or restart services.
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo "Run with sudo in the Pi terminal." >&2; exit 2; }
[[ $# -eq 1 ]] || { echo "Usage: $0 chatgpt|claude|gemini|codex" >&2; exit 2; }
case "$1" in chatgpt|claude|gemini|codex) CLIENT="$1";; *) echo "Unknown client" >&2; exit 2;; esac
OWNER=bchbenjamin
HOME_DIR="$(getent passwd "$OWNER" | cut -d: -f6)"
INSTALL=/opt/personal-ai
DB=/var/lib/pai-api/control-plane.sqlite3
DEST="$HOME_DIR/.config/personal-ai/external-brain"
FILE="$DEST/$CLIENT.token"
[[ -f "$DB" && -x "$INSTALL/.venv/bin/python" ]] || { echo "Existing installation not found." >&2; exit 2; }
[[ -n "$HOME_DIR" ]] || exit 2
install -d -o "$OWNER" -g "$(id -gn "$OWNER")" -m 0700 "$DEST"
if [[ -e "$FILE" || -L "$FILE" ]]; then
  echo "Credential already exists; retained unchanged at $FILE"
  exit 0
fi
CLIENT_ID="$CLIENT-external-$(date -u +%Y%m%dT%H%M%SZ)-$(cat /proc/sys/kernel/random/uuid)"
TMP="$(mktemp /run/pai-client.XXXXXXXX)"
trap 'rm -f "$TMP"' EXIT
# Initial client scopes exclude messaging writes, privileged approval and administration.
runuser -u pai-api -- env PAI_DB_PATH="$DB" PYTHONPATH="$INSTALL" \
  "$INSTALL/.venv/bin/python" -m personal_ai_api.cli issue-token \
  --client-id "$CLIENT_ID" --client-type external-brain \
  --scopes context:read,context:write,nodes:read,terminal:execute,box:read,box:execute,beeper:read,sessions:read > "$TMP"
grep -q '^pai_external-brain_[A-Za-z0-9_-]\+$' "$TMP" || { echo "Token issuance failed." >&2; exit 4; }
# Create atomically as the owner, with no clobber and no secret in arguments.
runuser -u "$OWNER" -- bash -c 'umask 077; set -o noclobber; cat > "$1"' bash "$FILE" < "$TMP"
echo "Created restricted credential: $FILE (not displayed)."
echo "Client ID: $CLIENT_ID"

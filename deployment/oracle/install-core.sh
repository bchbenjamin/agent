#!/usr/bin/env bash
# Fresh dedicated Debian/Ubuntu VM only; never run on the existing Pi.
set -Eeuo pipefail
umask 077
phase=preflight
trap 'rc=$?; echo "Cloud core install failed: phase=$phase line=$LINENO exit=$rc" >&2; exit "$rc"' ERR
[[ $EUID -eq 0 ]] || { echo "Run using sudo on the new Oracle VM." >&2; exit 2; }
[[ $# -le 2 ]] || { echo "Usage: $0 [--restore /protected/snapshot.sqlite3]" >&2; exit 2; }
restore=""
if [[ $# -ne 0 ]]; then
    [[ $# -eq 2 && "$1" == --restore && -f "$2" && ! -L "$2" ]] || exit 2
    restore="$(realpath "$2")"
fi
REPO="$(git -C "$(dirname "${BASH_SOURCE[0]}")/../.." rev-parse --show-toplevel)"
INSTALL=/opt/personal-ai
CONF=/etc/personal-ai
DB=/var/lib/pai-api/control-plane.sqlite3
[[ ! -e "$INSTALL" && ! -L "$INSTALL" && ! -e "$CONF" && ! -L "$CONF" && ! -e "$DB" ]] || { echo "Existing or partial installation detected; do not overwrite it." >&2; exit 2; }
if mountpoint -q /mnt/pi_data; then
    echo "Pi data mount detected; use the existing Pi runbook, not the cloud installer." >&2; exit 2
fi
[[ -z "$(git -C "$REPO" status --porcelain --untracked-files=no)" ]] || { echo "Use a clean reviewed checkout." >&2; exit 2; }
if [[ -n "$restore" ]]; then
    python3 "$REPO/deployment/backup/control-plane-snapshot.py" verify "$restore" --quiescent
fi
phase=packages
apt-get update
apt-get install -y python3 python3-venv curl git
phase=source
install -d -m 0755 "$INSTALL"
# Code and Python dependencies must be readable by the isolated service accounts.
# Keep the outer 077 umask for all private configuration and database files.
(
    umask 022
    git -C "$REPO" archive HEAD | tar --no-same-owner --no-same-permissions -xf - -C "$INSTALL"
    python3 -m venv "$INSTALL/.venv"
    "$INSTALL/.venv/bin/pip" install -r "$INSTALL/requirements.txt"
)
phase=accounts
for account in pai-api pai-mcp; do
    if ! id "$account" >/dev/null 2>&1; then
        useradd --system --user-group --home-dir "/var/lib/$account" --create-home --shell /usr/sbin/nologin "$account"
    fi
    install -d -o "$account" -g "$account" -m 0700 "/var/lib/$account"
done
install -d -m 0755 "$CONF"
phase=state
runuser -u pai-api -- test -x "$INSTALL/.venv/bin/python"
runuser -u pai-mcp -- test -r "$INSTALL/pai_mcp/server.py"
if [[ -n "$restore" ]]; then
    python3 "$INSTALL/deployment/backup/control-plane-snapshot.py" snapshot "$restore" "$DB" --quiescent
    chown pai-api:pai-api "$DB"
fi
# Generate a separate local administrator on the destination, without printing keys.
runuser -u pai-api -- env PAI_DB_PATH="$DB" PYTHONPATH="$INSTALL" \
  "$INSTALL/.venv/bin/python" -m personal_ai_api.cli issue-token \
  --client-id "oracle-admin-$(date -u +%Y%m%dT%H%M%SZ)" --client-type admin \
  --scopes nodes:admin,tasks:approve > "$CONF/admin-token"
chmod 0600 "$CONF/admin-token"
printf 'PAI_DB_PATH=%s\n' "$DB" > "$CONF/api.env"
# Enrollment is intentionally disabled. Restored Pi node tokens remain usable.
printf 'PAI_API_URL=http://127.0.0.1:8000\n' > "$CONF/mcp.env"
chown root:pai-api "$CONF/api.env"
chown root:pai-mcp "$CONF/mcp.env"
chmod 0640 "$CONF/"{api,mcp}.env
phase=services
install -m 0644 "$INSTALL/deployment/oracle/personal-ai-api.service" /etc/systemd/system/personal-ai-api.service
install -m 0644 "$INSTALL/deployment/systemd/personal-ai-mcp.service" /etc/systemd/system/personal-ai-mcp.service
systemctl daemon-reload
systemctl enable --now personal-ai-api.service personal-ai-mcp.service
phase=verification
for attempt in {1..20}; do
    if curl --noproxy '*' -fsS --max-time 2 http://127.0.0.1:8000/health >/dev/null 2>&1 &&
       [[ "$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' --max-time 2 http://127.0.0.1:8765/mcp)" == 401 ]]; then
        echo "Core API and authenticated MCP ready on loopback."
        echo "State: $DB; admin credential: $CONF/admin-token (not displayed)."
        echo "Configure private transport and verify actual client calls before public exposure."
        exit 0
    fi
    sleep 1
done
echo "Core readiness failed; inspect systemd status locally." >&2
exit 1

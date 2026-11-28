#!/usr/bin/env bash
# One-time, fail-closed migration of the existing Pi database to its root-FS
# service directory. This never initializes a replacement database.
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo "Run with sudo from the synchronized repository." >&2; exit 2; }
[[ $# -le 1 ]] || { echo "Usage: $0 [VERIFIED_DATABASE_OR_BACKUP]" >&2; exit 2; }
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEST=/var/lib/pai-api/control-plane.sqlite3
ENV_FILE=/etc/personal-ai/api.env
SOURCE="${1:-/mnt/pi_data/personal-ai/pai.sqlite3}"
[[ -f "$SOURCE" && ! -L "$SOURCE" ]] || { echo "Source database is missing or not a regular file; no state was changed." >&2; exit 3; }
if [[ "$SOURCE" == /mnt/pi_data/* ]]; then
  [[ "$(findmnt -n -o UUID --target /mnt/pi_data 2>/dev/null || true)" == cbdf283b-2951-44de-945e-c082bf87f337 ]] || {
    echo "The expected SSD is not mounted; refusing to inspect or migrate its mountpoint." >&2; exit 3;
  }
fi
[[ -s "$SOURCE" && -f "$ENV_FILE" && ! -e "$DEST" && ! -L "$DEST" ]] || {
  echo "Source/config missing or destination already exists; refusing overwrite or empty initialization." >&2; exit 3;
}
CURRENT="$(sed -n 's/^PAI_DB_PATH=//p' "$ENV_FILE" | head -1)"
[[ -n "$CURRENT" ]] || {
  echo "Configured database path is missing; review before proceeding." >&2; exit 3;
}
for unit in personal-ai-mcp.service personal-ai-api.service personal-ai-node.service; do
  state="$(systemctl show -p ActiveState --value "$unit")"
  [[ "$state" == inactive || "$state" == failed ]] || { echo "$unit must be stopped before migration." >&2; exit 3; }
done
install -d -o pai-api -g pai-api -m 0700 /var/lib/pai-api
install -d -o root -g root -m 0700 /var/backups/personal-ai
STAGE_DIR="$(mktemp -d /var/lib/pai-api/.migration.XXXXXXXX)"
STAGE="$STAGE_DIR/control-plane.sqlite3"
CONF_BACKUP="/var/backups/personal-ai/api.env.before-microsd.$(date -u +%Y%m%dT%H%M%SZ)"
UNIT_BACKUP="/var/backups/personal-ai/systemd-before-microsd.$(date -u +%Y%m%dT%H%M%SZ)"
cleanup() { rm -rf -- "$STAGE_DIR"; }
trap cleanup EXIT
python3 "$REPO/deployment/backup/control-plane-snapshot.py" snapshot "$SOURCE" "$STAGE"
chown pai-api:pai-api "$STAGE"
chmod 0600 "$STAGE"
install -o root -g pai-api -m 0640 "$ENV_FILE" "$CONF_BACKUP"
install -d -o root -g root -m 0700 "$UNIT_BACKUP"
for unit in personal-ai-api.service personal-ai-node.service; do
  install -o root -g root -m 0600 "/etc/systemd/system/$unit" "$UNIT_BACKUP/$unit"
done
python3 - "$ENV_FILE" <<'PY'
import grp, os, sys, tempfile
from pathlib import Path
p=Path(sys.argv[1]); lines=p.read_text().splitlines()
matches=[i for i,x in enumerate(lines) if x.startswith("PAI_DB_PATH=")]
if len(matches) != 1: raise SystemExit("Expected exactly one PAI_DB_PATH; no config changes made.")
lines[matches[0]]="PAI_DB_PATH=/var/lib/pai-api/control-plane.sqlite3"
fd,tmp=tempfile.mkstemp(prefix=".api.env.", dir=p.parent)
try:
    with os.fdopen(fd,"w") as f:
        f.write("\n".join(lines)+"\n"); f.flush(); os.fsync(f.fileno())
    os.chown(tmp,0,grp.getgrnam("pai-api").gr_gid); os.chmod(tmp,0o640)
    os.replace(tmp,p)
finally:
    if os.path.exists(tmp): os.unlink(tmp)
PY
mv -- "$STAGE" "$DEST"
rmdir "$STAGE_DIR"
trap - EXIT
install -o root -g root -m 0644 "$REPO/deployment/systemd/personal-ai-api.service" /etc/systemd/system/personal-ai-api.service
install -o root -g root -m 0644 "$REPO/deployment/systemd/personal-ai-node.service" /etc/systemd/system/personal-ai-node.service
systemctl daemon-reload
systemctl start personal-ai-api.service
for _ in $(seq 1 30); do
  curl --noproxy '*' -fsS --max-time 2 http://127.0.0.1:8000/health >/dev/null 2>&1 && break
  sleep 1
done
if ! curl --noproxy '*' -fsS --max-time 2 http://127.0.0.1:8000/health >/dev/null; then
  echo "API health failed. Source retained at $SOURCE; config backup: $CONF_BACKUP" >&2
  exit 4
fi
systemctl start personal-ai-mcp.service
systemctl restart personal-ai-node.service
echo "Migrated verified database to $DEST; source retained at $SOURCE; config backup at $CONF_BACKUP."
echo "Verify existing client authentication and audit chain before enabling dependent integrations."

#!/usr/bin/env bash
# Owner-run Pi migration export. Requires stopped control-plane and Hermes
# writers, a valid database on microSD, age, and an owner-controlled recipient.
# Output is an encrypted archive; no plaintext tar archive is created.
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 && $# -eq 2 ]] || {
    echo "Usage (sudo): $0 AGE_RECIPIENT_FILE /protected/output.tar.gz.age" >&2; exit 2;
}
RECIPIENTS="$(realpath "$1")"
DEST="$(realpath -m "$2")"
[[ -s "$RECIPIENTS" && "$DEST" == *.tar.gz.age && ! -e "$DEST" && ! -L "$DEST" ]] || exit 2
[[ -d "$(dirname "$DEST")" ]] || exit 2
command -v age >/dev/null || { echo "Install age from the OS package repository first." >&2; exit 2; }
OWNER=bchbenjamin
OWNER_HOME="$(getent passwd "$OWNER" | cut -d: -f6)"
[[ -d "$OWNER_HOME/.hermes-pi" && ! -L "$OWNER_HOME/.hermes-pi" ]] || { echo "Inspect canonical Hermes runtime path first." >&2; exit 2; }
# Fail closed if an expected writer is still active or in transition.
for unit in personal-ai-api.service personal-ai-mcp.service personal-ai-node.service; do
    state="$(systemctl show -p ActiveState --value "$unit")"
    [[ "$state" == inactive || "$state" == failed ]] || { echo "Stop and drain $unit before export." >&2; exit 2; }
done
uid="$(id -u "$OWNER")"
hermes_unit=hermes-gateway-e86e8d0b.service
state="$(runuser -u "$OWNER" -- env XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user show -p ActiveState --value "$hermes_unit")"
[[ "$state" == inactive || "$state" == failed ]] || { echo "Stop the canonical Hermes gateway before export." >&2; exit 2; }
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STAGING="$(mktemp -d /var/lib/pai-api/.migration-stage.XXXXXXXX)"
PART=""
cleanup() {
    rm -rf -- "$STAGING"
    [[ -z "$PART" ]] || rm -f -- "$PART"
}
trap cleanup EXIT
python3 "$REPO/deployment/backup/control-plane-snapshot.py" snapshot \
    /var/lib/pai-api/control-plane.sqlite3 "$STAGING/control-plane.sqlite3" --quiescent
if [[ -d /var/lib/pai-agent/pending-results ]] &&
   [[ -n "$(find /var/lib/pai-agent/pending-results -maxdepth 1 -type f -print -quit)" ]]; then
    echo "Pending node results remain; reconcile before exporting." >&2
    exit 2
fi
# Only specifically identified runtime/config directories, no browser profile,
# Beeper database, system home or application/venv directory.
paths=("etc/personal-ai" "${OWNER_HOME#/}/.hermes-pi")
for p in "${OWNER_HOME#/}/.config/personal-ai" "${OWNER_HOME#/}/.config/systemd/user" "var/lib/pai-agent/node-token"; do
    [[ ! -e "/$p" ]] || paths+=("$p")
done
git -C "$REPO" rev-parse HEAD > "$STAGING/source-revision.txt"
PART="$(mktemp "$(dirname "$DEST")/.migration-encrypted.XXXXXXXX")"
tar -czf - -C "$STAGING" control-plane.sqlite3 source-revision.txt -C / "${paths[@]}" | age -R "$RECIPIENTS" > "$PART"
chmod 0600 "$PART"
# No overwrite even if another process creates the final path during export.
ln "$PART" "$DEST"
echo "Encrypted migration bundle created: $DEST"
echo "Verify decryption privately with your recovery key before transferring or cutover."

# Raspberry Pi 5 Operational Runbook

## Host information

- Hardware: Raspberry Pi 5 Model B, 4 GB RAM.
- OS: Debian GNU/Linux 13 (trixie), aarch64.
- Primary user: bchbenjamin (UID 1000).
- Boot drive: 64 GB microSD (mmcblk0), permanent boot device.
- Optional bulk data drive: 256 GB OSC SATA SSD, mounted at /mnt/pi_data when available.
- SSD data filesystem: ext4, label PI_DATA, UUID recorded in nodes/pi5/node-spec.yaml.

The SSD is optional bulk storage. No essential service may require it. Core state, including the API database and node result spool, is on the microSD under `/var/lib`. Do not format or repartition the SSD; if it is absent or unstable, continue operating from the boot volume and recover it separately.

## Pre-deployment checks

1. Inspect the actual device and mount table.
2. Confirm the Beeper data recovery/backup is verified.
3. If present, confirm the optional SSD UUID and fstab nofail entry match the node specification.
4. Confirm Tailscale and KDE Connect are healthy.
5. Confirm Hermes, Beeper and computer-use-linux still work locally.
6. Confirm the AI Gateway and Claude Code credentials/configuration are unchanged.
7. Save a current backup before deployment.

Do not run the installer until those checks are complete.

## Install Personal AI

Run from the repository checkout as bchbenjamin, not root:

    bash deployment/install/install-personal-ai.sh

The installer:
- Installs Python dependencies in /opt/personal-ai/.venv.
- Deploys files from the checked-out Git commit into a root-owned directory readable by the service accounts.
- Creates dedicated pai-api, pai-mcp and pai-agent system accounts; the SQLite database is private to pai-api.
- Stores the initial admin token root-only at /etc/personal-ai/admin-token.
- Creates a dedicated pai-agent system account; its node token lives at /var/lib/pai-agent/node-token (mode 0600).
- Runs the daemon as pai-agent and launches approved task processes as bchbenjamin through the root-owned fixed helper. The task process cannot read the pai-agent token directory or the API database.
- Stores the SQLite control-plane database on `/var/lib/pai-api/control-plane.sqlite3` on the permanent microSD. The SSD is not required.
- Installs the API, MCP and node-agent systemd services.
- Installs the root-owned, fixed-command systemd helper and sudoers rule.
- Enrolls the Pi node with an API-issued node credential.
- Does not format drives, alter the boot device, change Tailscale configuration or modify the AI Gateway.

The installer reports the path of the root-only admin token at `/etc/personal-ai/admin-token`. Retrieve the token from a private administrator terminal only when needed. The API database is owned by pai-api and is not readable by the node-agent task identity.

For an existing install, run
`bash deployment/install/install-pi-recovery.sh` as the owner from the
checkout. It can be run without the SSD mounted. It points the stable `~/Applications/Beeper.AppImage` path at
the newest installed ARM64 AppImage, then installs the graphical-session-aware
system unit. Current installers do not enable the legacy SSD recovery timer. It does not stop or start Beeper when a desktop process is open.

## Services

System services:

    systemctl status personal-ai-api.service personal-ai-mcp.service personal-ai-node.service
    systemctl status beeper.service lightdm.service wayvnc.service tailscaled.service

Hermes user services:

    systemctl --user status hermes-gateway-e86e8d0b.service at-spi-dbus-bus.service

Local health:

    curl -fsS http://127.0.0.1:8000/health
    curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:23373/v0/mcp

The Beeper endpoint is OAuth-protected; HTTP 401 without an OAuth token can indicate that the local endpoint is running.

## Client credentials and Hermes

On the Pi, `~/.hermes-pi` is the runtime home for configuration, credentials,
pairing, integrations, memory, and sessions. The CLI launcher in `~/.local/bin`
and the Hermes gateway user unit use that home. The application checkout,
managed Python, and installer assets remain under `~/.hermes`.

Telegram polling belongs to the Pi gateway. Keep the bot token in the
runtime's private `.env` as `TELEGRAM_BOT_TOKEN` and allowlist the verified
numeric owner with `TELEGRAM_ALLOWED_USERS`. The Pi uses allowlist-only
direct messages and disables group access. Keep the Simular Box as an
HTTPS MCP integration and leave Telegram polling disabled there.

Issue separate tokens for Hermes and every external MCP client. Morphic chat uses the separate Hermes downstream API key; only a future direct Personal AI operations panel needs a scoped Personal AI client token. Run token administration as pai-api because the SQLite database is not accessible to bchbenjamin or the node-agent account. Do not reuse the AI Gateway key.

Example:

    sudo -u pai-api env PAI_DB_PATH=/var/lib/pai-api/control-plane.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli issue-token --client-id hermes-agent --client-type hermes --user owner --scopes context:read,nodes:read,files:read,terminal:execute,services:manage

Issue a separate context:write-only token for the indexer:

    sudo -u pai-api env PAI_DB_PATH=/var/lib/pai-api/control-plane.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli issue-token --client-id context-indexer --client-type indexer --user owner --scopes context:write

Save the returned token mode 0600 at ~/.config/personal-ai/context-index-token. Run the indexer as bchbenjamin with PAI_API_URL=http://127.0.0.1:8000 and PAI_CONTEXT_INDEX_ROOTS set to approved roots:

    PAI_API_URL=http://127.0.0.1:8000 PAI_CONTEXT_INDEX_ROOTS="$HOME/Documents" /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli index-path --path "$HOME/Documents"

The indexer submits files to the API; it does not open the database.

Put the Hermes-specific token in the Hermes environment file as PAI_API_TOKEN (mode 0600), then add the Personal AI MCP endpoint from integrations/hermes/config.template.yaml. Keep Beeper OAuth and computer-use-linux stdio MCP local to Hermes.

If computer-use-linux is not already installed, use the upstream Hermes integration:

    npm install -g @agent-sh/computer-use-linux
    hermes skills tap add agent-sh/computer-use-linux
    hermes skills install agent-sh/computer-use-linux/computer-use-linux
    hermes mcp add computer-use-linux --command computer-use-linux --args mcp
    hermes mcp test computer-use-linux

The MCP server controls the live desktop; keep it local and review mutating actions. The existing native Wayland Computer Use configuration is preserved, so verify the final tool list and avoid duplicate overlapping controllers.

## Audit and context

    sudo -u pai-api env PAI_DB_PATH=/var/lib/pai-api/control-plane.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli verify-audit

Set explicit context index roots before running index-path. Do not index Beeper databases, keyrings, environment files, OAuth tokens or private credentials.

## Health verification

Run:

    bash nodes/pi5/verify.sh

The verification script also reports pre-existing Hermes, Beeper, computer-use-linux and storage conditions. Investigate warnings before declaring deployment complete.

## Existing Pi: guarded SSD-to-microSD database migration

The ordinary installer is not a migration tool. It refuses an existing
installation whose configured database is missing or fails schema, SQLite,
foreign-key, or audit-chain validation. Do not point the API at a new path
until the original control-plane DB or a verified backup is available.

After the original SSD is stable and mounted with its recorded UUID (or a
verified backup is staged in a protected local file), drain/reconcile queued,
running, and approval-required tasks. Stop `personal-ai-mcp.service`,
`personal-ai-api.service`, and `personal-ai-node.service`, then run from the synchronized checkout:

    sudo bash deployment/install/migrate-control-plane-to-microsd.sh

For an independently verified backup at another protected path, pass that
path as the sole argument. The script requires the destination not to exist,
uses SQLite's online backup API, validates the Personal AI schema and audit
chain, preserves the source, updates only `PAI_DB_PATH`, backs up the current
API environment and unit files under `/var/backups/personal-ai`, installs the
microSD-backed API/node units, then starts API, MCP, and node in dependency
order. Verify existing client authentication, audit chain, context, task
state, and node heartbeat before cleanup. Keep the original SSD database and
pre-migration backups until those checks pass. No reboot is part of migration.

Rollback: stop MCP/API/node; restore `/etc/personal-ai/api.env` and the two
unit files from the timestamped `api.env.before-microsd.*` and
`systemd-before-microsd.*` backups; run `systemctl daemon-reload`; restore the
old DB path in `PAI_DB_PATH` and start services only after the original source
is mounted and verified. The migrated copy is retained at
`/var/lib/pai-api/control-plane.sqlite3`; do not delete either copy during
rollback.

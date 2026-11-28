# Raspberry Pi 5 Operational Runbook

## Host information

- Hardware: Raspberry Pi 5 Model B, 4 GB RAM.
- OS: Debian GNU/Linux 13 (trixie), aarch64.
- Primary user: bchbenjamin (UID 1000).
- Boot drive: 64 GB microSD (mmcblk0), permanent boot device.
- Secondary data drive: 256 GB OSC SATA SSD, mounted at /mnt/pi_data.
- SSD data filesystem: ext4, label PI_DATA, UUID recorded in nodes/pi5/node-spec.yaml.

The SSD is data-only. Never format or repartition it as part of normal deployment. The installer refuses to continue unless /mnt/pi_data is already mounted.

The API and MCP units remain guarded by `RequiresMountsFor=/mnt/pi_data` and
`ConditionPathIsMountPoint=/mnt/pi_data`. The enabled
`personal-ai-storage-recovery.timer` starts the API and MCP only after fstab
has mounted the expected UUID and the API health check passes. It does not
mount or fsck a device. If the SSD is absent at boot, first stabilize and
verify the power/cable/enclosure and filesystem, then mount the expected
volume; the timer will recover services after that. Never run filesystem
repair against an unstable or unverified device.

## Pre-deployment checks

1. Inspect the actual device and mount table.
2. Confirm the Beeper data recovery/backup is verified.
3. Confirm the SSD's UUID and fstab nofail entry match the node specification.
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
- Stores the SQLite control-plane database on /mnt/pi_data/personal-ai.
- Installs the API, MCP and node-agent systemd services.
- Installs the root-owned, fixed-command systemd helper and sudoers rule.
- Enrolls the Pi node with an API-issued node credential.
- Does not format drives, alter the boot device, change Tailscale configuration or modify the AI Gateway.

The installer reports the path of the root-only admin token at `/etc/personal-ai/admin-token`. Retrieve the token from a private administrator terminal only when needed. The API database is owned by pai-api and is not readable by the node-agent task identity.

For an existing install, run
`bash deployment/install/install-pi-recovery.sh` as the owner from the
checkout. It can be run without the SSD mounted. It installs/enables the
service recovery timer and points the stable `~/Applications/Beeper.AppImage` path at
the newest installed ARM64 AppImage, then installs the graphical-session-aware
system unit. It does not stop or start Beeper when a desktop process is open.

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

    sudo -u pai-api env PAI_DB_PATH=/mnt/pi_data/personal-ai/pai.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli issue-token --client-id hermes-agent --client-type hermes --user owner --scopes context:read,nodes:read,files:read,terminal:execute,services:manage

Issue a separate context:write-only token for the indexer:

    sudo -u pai-api env PAI_DB_PATH=/mnt/pi_data/personal-ai/pai.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli issue-token --client-id context-indexer --client-type indexer --user owner --scopes context:write

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

    sudo -u pai-api env PAI_DB_PATH=/mnt/pi_data/personal-ai/pai.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli verify-audit

Set explicit context index roots before running index-path. Do not index Beeper databases, keyrings, environment files, OAuth tokens or private credentials.

## Health verification

Run:

    bash nodes/pi5/verify.sh

The verification script also reports pre-existing Hermes, Beeper, computer-use-linux and storage conditions. Investigate warnings before declaring deployment complete.

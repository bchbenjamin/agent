# Oracle migration and disaster recovery

## Scope and decision

Oracle will host Layer 2 (Personal AI control plane, shared context, MCP and
eventually the canonical Hermes runtime). The independent inference Gateway
at ai.bchbenjamin.in is not migrated or granted device access. Oracle is not
yet provisioned; no quota, shape availability, pricing or free eligibility is
assumed. Prefer a supported ARM64 Debian/Ubuntu image if available; x86_64
also works for the Python core. Select a persistent boot/data volume with
room for the databases and encrypted backups. This does not require a Pi SSD,
Raspberry Pi kernel, graphical session or user UID 1000.

| Component | Now | Target |
|---|---|---|
| Personal AI API/SQLite | Pi microSD (`/var/lib/pai-api`) | Oracle persistent volume, single writer |
| External MCP | Pi, Render relay | Oracle direct HTTPS ingress; Pi bridge retained for local integrations until federation is tested |
| Hermes native runtime | Pi, ~/.hermes-pi | Oracle after a separate quiesced state migration |
| Telegram | Pi Hermes polling | Exactly one canonical Hermes poller, eventually Oracle |
| Beeper and Wayland | Pi | Pi, accessed through explicitly authenticated private tools |
| Simular Box | Existing HTTPS MCP | Same provider, dedicated authorized credential |
| Redmi whyred | Planned native Termux inference | Same private inference node |
| Morphic | Existing Vercel deployment | Same frontend, change upstream only after tests |
| ChatGPT private plugin | Existing account plugin | Update endpoint, not recreate plugin |

## Phase 0 — capture and rehearse

1. Run the [Pi recovery checks](pi5-runbook.md), including an authenticated
   MCP discovery and real hostname task. Record actual deployed revision,
   service enablement and remaining integration failures, not raw secrets.
   Confirm the Pi's service recovery timer and exact UUID mount as well; API/MCP
   health without the data volume is not an acceptable recovery state. The
   timer must not mount or repair an unstable volume.
2. On the Pi, use the new online SQLite snapshot command as owner-approved
   administrator:
   ```sh
   sudo install -d -o pai-api -g pai-api -m 0700 /var/backups/personal-ai
   sudo python3 deployment/backup/control-plane-snapshot.py snapshot \
     /var/lib/pai-api/control-plane.sqlite3 \
     /var/backups/personal-ai/pai-rehearsal.sqlite3
   ```
   A rehearsal copy contains private memory and hashed credentials; encrypt
   before off-device transfer. Keep it private and do not expose rehearsal
   services or attach production workers. Use age with an owner-controlled
   recipient/public key and verify decryption on a private host, or another
   reviewed authenticated encryption workflow. Store recovery keys separately
   from encrypted backups. Never upload unencrypted data to Git or Box.
3. Make separate protected backups of the canonical Hermes runtime
   `~/.hermes-pi` (including config, .env, native memory, sessions, skills,
   OAuth state and pairing), the existing service unit/drop-ins, client
   token files under `~/.config/personal-ai`, and node configuration. Stop
   the canonical Hermes user service during the final filesystem backup so
   SQLite and related WAL files are consistent; preserve permissions and
   inspect the actual installed paths. Do not archive ~/.hermes dependencies,
   unrelated home directories, Beeper profile or browser passwords for
   routine cloud migration. Beeper stays on the Pi; back it up separately
   under the owner's control. Treat these archives as secrets.
4. On a fresh isolated VM, clone this repository, review the commit and run
   the cloud core installer against synthetic data first. Do not use the
   Pi's first-install script on Oracle.

## Phase 1 — final control-plane migration

Stop accepting new tasks: disconnect external clients and disable ingress
before taking the final snapshot. Drain queued, approval-required and running
tasks with the owner. Verify the node's pending result spool is empty; never
replay uncertain commands or delete undelivered results. Stop the Pi node
agent and old API/MCP writers only after drain. Keep the old services stopped
until rollback or an explicit cutover plan.

```sh
sudo python3 deployment/backup/control-plane-snapshot.py snapshot \
  /var/lib/pai-api/control-plane.sqlite3 \
  /var/backups/personal-ai/pai-final.sqlite3 --quiescent
```

Transfer the encrypted snapshot to the new VM over authenticated transport.
Decrypt into a protected directory. Verify file integrity and the task
status counts. Do not copy a live SQLite file alone or keep two writable
copies.

On the **new** Oracle VM only:

```sh
git clone https://github.com/bchbenjamin/agent.git ~/personal-ai-infrastructure
cd ~/personal-ai-infrastructure
sudo bash deployment/oracle/install-core.sh --restore /protected/pai-final.sqlite3
```

For a fresh empty deployment omit --restore. The installer provisions isolated
service accounts, installs dependencies, verifies the database and enables
loopback-only API/MCP system services. It refuses existing installations.
A new local administrator token is generated; restored scoped client and node
tokens are preserved by their stored hashes. Existing Pi-side token files
must be kept. No fresh node enrollment is enabled by default. Verify the
admin credential and audit chain locally, then verify an existing external
client token against the destination. Revoke stale credentials explicitly.

If the installer fails, inspect its reported phase and service logs locally;
do not delete a partial installation or re-run blindly.

## Phase 2 — reconnect Pi and publish the MCP

Start with a private Tailscale or verified SSH transport. Do not open TCP
8000 or 8765 to the Internet. One supported topology, after establishing
SSH on the VM and authenticating the Pi's dedicated tunnel key, is:

- Pi local forward 127.0.0.1:18000 -> Oracle 127.0.0.1:8000 for the node
  agent and Pi-side MCP adapter. Use the existing node credential, set
  PAI_API_URL=http://127.0.0.1:18000 in their protected environment files,
  then start the node and MCP services. Verify real heartbeat and task output.
- Pi reverse forward Oracle 127.0.0.1:18765 -> Pi 127.0.0.1:8765 for the
  Pi integration MCP if needed. Keep the Oracle listener on loopback
  (GatewayPorts disabled); restrict tunnel accounts and permitted forwarding
  addresses, verify server host key. Example command for an already
  authorized SSH user (replace OCI_HOST and user):
  ```sh
  ssh -NT -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
    -L 127.0.0.1:18000:127.0.0.1:8000 \
    -R 127.0.0.1:18765:127.0.0.1:8765 tunnel-user@OCI_HOST
  ```
  Run under an enabled, dedicated systemd service after manual acceptance;
  document actual account, key path and host key fingerprint locally.
  This is a proposed transport, not installed or tested.
- An Oracle-local MCP at 8765 can access Oracle context/tasks but not Pi's
  loopback Beeper or Hermes API. In the initial control-plane-only migration,
  expose the Pi-side MCP through the reverse forward if those integrations
  must remain available. Full remote federation is still pending; do not
  imply that Oracle-local MCP already provides Pi desktop or messaging.
- After verifying TLS and bearer authentication, configure the proposed
  mcp.hermes.bchbenjamin.in DNS and Caddy site with the template in
  deployment/oracle/Caddyfile.mcp.template. Choose 8765 for cloud-core
  MCP or 18765 for the Pi bridge after a successful private test. Allow only
  necessary HTTPS/ACME and restricted administration traffic in both OCI
  security rules and host firewall. Never publish enrollment or approval
  endpoints. Do not modify the inference gateway DNS or Vercel portfolio.

Update the existing private ChatGPT plugin configuration and Claude
connectors after the new endpoint passes live discovery. Preserve plugin
identity and client credentials; update Morphic separately. Retire the old
Render relay only after all clients pass. Gemini requires a compatible OAuth
flow; the bearer-only implementation does not currently satisfy its web UI.

## Phase 3 — move Hermes native runtime separately

Install the reviewed Hermes upstream version from upstreams/manifest.yaml
and compare with the actual Pi version. Restore the protected canonical
runtime home into the new owner's home with correct ownership; restore
configuration and keys through the owner's secret store. Do not copy venvs
or architecture-specific binaries. Adapt absolute paths, native API bind
address and MCP URLs for the target. Start with Telegram polling disabled;
do not create a second consumer of the same bot. Verify native history,
memory, actual tool continuation, owner approval, Morphic session behavior
and private MCP integration with the Pi. Only then stop the Pi Hermes
gateway and activate the Oracle poller. If Beeper OAuth cannot be reused,
re-authorize on the Pi through its supported flow. Keep desktop control
local; an Oracle server cannot directly inherit Pi Wayland sockets.
Do not modify the Gateway provider or credentials.

## Acceptance and rollback

- API health, 401 for missing/invalid auth, MCP initialize and 13 baseline
  tools, correct client scopes, owner-only approval.
- Real Pi hostname task, separate Box health probe, Beeper discovery,
  native history and approved shared context write/read across clients.
- Confirm inference is not invoked by direct MCP tools.
- Restart API/MCP, reconnect tunnel, reboot VM and Pi, verify enabled
  services, mounts, memory, task state and node heartbeat.
- Verify exactly one Telegram poller and real frontend session continuity.
- Verify encrypted backup restoration on a disposable private destination.
- If cutover fails before new writes, stop Oracle writers and reconnect
  Pi clients to original API. If Oracle accepted writes, snapshot its
  quiescent state and reconcile/restore before restarting the old Pi;
  never silently discard new history or replay completed tasks.
- Full Box shell/files, Pi desktop federation, Beeper writes, native memory
  synchronization, Gemini OAuth and bulk conversation imports remain
  feature work, not completed migration capabilities.

Record each result with exact revision and timestamp. Do not declare Oracle
ready solely because the installer or local test suite succeeds.

### Encrypted final recovery bundle

After the phase-1 drain and shutdown, also stop the canonical Hermes user
gateway (and any other processes writing its state). Install age from the
OS package repository and supply an owner-controlled file of age public
recipients. Use a private destination on mounted persistent storage:

```sh
sudo bash deployment/backup/prepare-migration-bundle.sh \
  /path/to/age-public-recipients.txt \
  /var/backups/personal-ai/hermes-final.tar.gz.age
```

This is optional and intentionally requires stopped services. It includes
the consistent control-plane snapshot, source revision, the protected
Personal AI configuration, canonical Hermes runtime and available client,
node and user-systemd configuration. It does not archive a Beeper profile,
browser passwords or the application venv. The temporary SQLite snapshot is
protected on the microSD and cleaned up; the final archive is encrypted. Check
for state symlinks and external dependencies before relying on the bundle.
Do not copy the age private key alongside the backup. Verify decryption
and inspect the archive in a protected staging directory; never extract
the bundle directly over an active Oracle or Pi installation. Restore
individual components with the runbook and correct ownership. This helper
has not been executed with actual Pi state.

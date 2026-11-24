# Personal AI Infrastructure

Canonical repository for the owner's personal agent control plane, node execution, MCP integration and deployment.

## Architecture

The design has two isolated layers:

1. **AI Gateway — https://ai.bchbenjamin.in**: model inference and provider routing only. It has no access to personal files, credentials, messages, memory, devices or node-management APIs.
2. **Personal AI — Layer 2**:
   - https://hermes.bchbenjamin.in: Morphic chat UI.
   - https://api.hermes.bchbenjamin.in: authenticated Personal AI API and control plane.
   - https://mcp.hermes.bchbenjamin.in/mcp: authenticated MCP Streamable HTTP adapter.

Hermes is the agent runtime and shared context/memory layer. The Raspberry Pi 5 is the primary node. Simular Box is an auxiliary execution/browser node. Redmi remains staged for future work.

The API and MCP adapter do not route personal context to the AI Gateway. Nodes call the gateway for inference independently; the gateway cannot initiate calls into Layer 2.

## Runtime components

| Component | Implementation |
|---|---|
| Personal AI API | FastAPI, personal-ai-api/ |
| Persistence | SQLite with WAL; tokens stored as SHA-256 hashes |
| Authentication | Per-client bearer tokens and per-node credentials |
| Authorization | Central scopes in control-plane/authorization/scopes.py |
| Task queue | Persistent outbound-poll queue; nodes need no inbound port |
| Node agent | Unprivileged Python daemon in node-agent/ |
| Privileged helper | Fixed systemd service allowlist only; no arbitrary root shell |
| Audit | Persistent append-only SHA-256 hash chain |
| Context | Explicitly indexed text documents, queried through scoped API |
| MCP | Official Python MCP SDK in pai_mcp/; stdio and Streamable HTTP |
| Existing local tools | Beeper OAuth MCP and upstream computer-use-linux stdio MCP remain local to Hermes/Pi |

## API surface

All endpoints except /health require authentication unless they are explicitly node-enrollment endpoints.

| Method | Path | Purpose |
|---|---|---|
| GET | /health | Liveness |
| GET | /v1/auth/me | Validate token and inspect its client/scopes |
| GET | /v1/nodes | List nodes and online/offline status |
| GET | /v1/nodes/{node_id} | Node details |
| DELETE | /v1/nodes/{node_id} | Revoke a node credential (nodes:admin) |
| POST | /v1/nodes/register | Enroll a node using X-Node-Enrollment-Token |
| POST | /v1/nodes/{node_id}/heartbeat | Node-authenticated heartbeat |
| POST | /v1/nodes/{node_id}/tasks/next | Outbound task polling |
| POST | /v1/nodes/{node_id}/tasks/{task_id}/result | Node result report |
| POST | /v1/tasks | Submit a scoped task |
| GET | /v1/tasks/{task_id} | Retrieve task state/result |
| GET | /v1/tasks/pending-approval | List tasks awaiting approval (tasks:approve) |
| POST | /v1/tasks/{task_id}/approve | Approve a high-impact task |
| POST | /v1/context/index | Add a document with context:write |
| POST | /v1/context/query | Search indexed context |

Supported task operations: exec (argv, no shell), shell (explicit approval required), service_status, and service_restart (approval required). Beeper and computer-use remain first-class local Hermes MCP integrations; the Personal AI node agent does not impersonate or replace their upstream MCP servers.

## Security model

- Client tokens are random, stored as SHA-256 hashes, scoped independently and revocable.
- The API database belongs to the dedicated pai-api account; MCP and node-agent processes cannot read it.
- The initial admin token is stored root-only at /etc/personal-ai/admin-token; task processes cannot read it.
- Context indexing uses a separate context:write token and an explicit root allowlist.
- Node tokens are random, stored as hashes and returned only once at enrollment.
- The daemon runs as a dedicated pai-agent account; task processes run as bchbenjamin through the fixed helper, never as root.
- Normal command execution uses argv with shell=False; explicit shell and sensitive commands require a separate approval.
- The root-owned helper accepts only fixed systemd actions or execution as the normal bchbenjamin user. It is not a general-purpose root command runner; node credentials remain inaccessible to task processes.
- MCP HTTP requests must carry an API-issued Bearer token. MCP forwards that token to the API; authorization is not duplicated in the adapter.
- Audit events are hash-chained and persisted with the operational database.
- The database belongs on /mnt/pi_data, not the permanent microSD boot device.
- No unauthenticated public MCP endpoint is supported.

## Development on the Simular Box

Create a Python virtual environment, install requirements.txt, set PAI_DB_PATH to a local development SQLite file and set PAI_BOOTSTRAP_TOKEN to a random secret. Run the API with:

    uvicorn personal_ai_api.server.app:app --host 127.0.0.1 --port 8000

In another terminal, set PAI_API_URL=http://127.0.0.1:8000, PAI_MCP_TRANSPORT=streamable-http, PAI_MCP_HOST=127.0.0.1 and PAI_MCP_PORT=8765, then run:

    python -m pai_mcp.server

For local stdio MCP, set PAI_API_TOKEN to a client-scoped token and use PAI_MCP_TRANSPORT=stdio.

Issue production client tokens through the pai-api account:

    sudo -u pai-api env PAI_DB_PATH=/mnt/pi_data/personal-ai/pai.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli issue-token --client-id hermes-agent --client-type hermes --user owner --scopes context:read,nodes:read,files:read,terminal:execute,services:manage

Issue a separate context-index token with only context:write:

    sudo -u pai-api env PAI_DB_PATH=/mnt/pi_data/personal-ai/pai.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli issue-token --client-id context-indexer --client-type indexer --user owner --scopes context:write

Save it mode 0600 at ~/.config/personal-ai/context-index-token, then index approved text files:

    PAI_API_URL=http://127.0.0.1:8000 PAI_CONTEXT_INDEX_ROOTS="$HOME/Documents" /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli index-path --path "$HOME/Documents"

The indexer reads files as the user and submits documents to the API; it does not need direct database access.

Run local tests:

    pytest -q tests/unit tests/security
    pytest -q

External live-service tests are opt-in with PAI_RUN_EXTERNAL_INTEGRATION=1.

## Raspberry Pi deployment

The Pi's boot drive remains the 64 GB microSD. The 256 GB OSC SSD is data-only and must already be mounted at /mnt/pi_data. The installer refuses to continue if that mount is absent.

After verifying the SSD backup/recovery state and checking the current Pi services, run as bchbenjamin:

    bash deployment/install/install-personal-ai.sh

The script installs API, MCP and node-agent systemd services, a restricted systemd helper and private database storage. It does not format or repartition any drive. Review docs/deployment/pi5-runbook.md before deployment.

## Repository map

- control-plane/: persistence, authentication, scopes, node registry and audit.
- personal-ai-api/: FastAPI routes and administrative CLI.
- node-agent/: outbound node daemon and command/service execution.
- pai_mcp/: official MCP SDK adapter.
- integrations/: AI Gateway, Hermes, Beeper, Morphic, Box and computer-use references.
- nodes/: node specifications and provisioning scripts.
- deployment/: systemd, installation, restricted helper, backup, upgrade and rollback.
- docs/: architecture decisions, threat model and operational runbooks.
- tests/: unit, integration and security checks.

## Current implementation status

The API, persistent store, client/node authentication, approval queue, node polling protocol, task execution runner, audit chain and MCP adapter are implemented and locally smoke-tested. Production DNS/reverse-proxy configuration, Pi deployment, Hermes OAuth/MCP login, actual Beeper/computer-use end-to-end tests, and encrypted off-device backup verification remain deployment tasks.

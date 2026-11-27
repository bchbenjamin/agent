# Architecture Specification

## 1. Architectural philosophy

The system separates model inference from personal state and uses a central control plane with edge execution.

- External models receive only prompt context explicitly sent by the agent.
- The AI Gateway is a separate inference-only service.
- Personal AI owns client authentication, scopes, approvals, task state, context indexing, node registry and audit.
- Nodes initiate outbound requests and poll the API; no inbound node listener is required.

## 2. Two isolated layers

Layer 1 — AI Gateway: https://ai.bchbenjamin.in
- Independent inference router and provider gateway.
- OpenAI-compatible endpoints under /codex/v1.
- Authenticates inference clients only.
- No access to Personal AI API, personal files, nodes, databases or memory.

Layer 2 — Personal AI:
- https://hermes.bchbenjamin.in — Morphic chat UI.
- https://ai.bchbenjamin.in/_ingress/http/api — outbound Pi connector relay for the Hermes API and Personal AI control plane.
- https://ai.bchbenjamin.in/_ingress/http/mcp/mcp — authenticated MCP adapter relay.
- Hermes is the agent runtime and shared context/memory layer.
- Pi 5 is the primary node; Simular Box is auxiliary; Redmi is staged.

## 3. Control plane and MCP

The FastAPI service runs as pai-api and authenticates clients, checks scopes, creates tasks, manages approvals, records audit events and exposes indexed context. SQLite is stored on the SSD and owned by pai-api; the pai-mcp and pai-agent accounts cannot read it. The separate indexer client reads approved user files and submits documents with a context:write-only token.

The MCP server uses the official Python MCP SDK. It is a protocol adapter only:
- Each HTTP MCP request must carry an API-issued Bearer token.
- The adapter validates and forwards that same token to the Personal AI API.
- It does not implement a second authorization policy or execute commands locally.
- stdio mode uses a client-scoped token from its environment.

## 4. Node agent execution model

Each managed node runs a dedicated unprivileged pai-agent daemon.
1. The daemon stores its node credential under /var/lib/pai-agent; task processes cannot read that directory.
2. The daemon sends heartbeats and polls the API for queued tasks.
3. Normal command execution uses argv and shell=False.
4. Explicit shell and sensitive commands require a separate approval before dispatch.
5. The daemon uses a root-owned helper to execute approved user tasks as bchbenjamin or restart allowlisted system services. It never exposes arbitrary root execution.
6. The task process runs as bchbenjamin and can access the user's ordinary files; it is not granted root.
7. Results are first persisted under /var/lib/pai-agent/pending-results, then returned to the API. The spool retries after API restarts.
8. Audit summaries are recorded without logging command output.

## 5. Pi 5 placement

The Raspberry Pi 5 hosts the Personal AI API/control plane, MCP adapter, pai-agent daemon, Hermes runtime and Beeper Desktop. Beeper's OAuth MCP endpoint remains bound to 127.0.0.1:23373. Hermes Computer Use remains local to the Pi's Wayland desktop. The 256 GB OSC SSD is data-only at /mnt/pi_data; the 64 GB microSD remains the permanent boot device.

Hermes uses the Simular Box as an auxiliary execution and browser environment through authenticated HTTPS MCP. This connection originates from Hermes and does not require Box-to-Pi SSH. Oracle is the planned primary Layer 2 host; a quiescent database migration preserves existing scoped client/node token hashes. Pi execution and Beeper/Wayland remain on the Pi through authenticated private transport. Redmi is a dedicated native Termux inference node, not a personal-context worker. See docs/deployment/oracle-migration.md for staged migration, limitations and rollback.

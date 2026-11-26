# Network Topology & Domain Routing

## Domain Layout

| Domain | Role | Ingress Route | Destination |
|---|---|---|---|
| ai.bchbenjamin.in | Layer 1 inference-only gateway | Existing independent deployment | AI Gateway inference service |
| hermes.bchbenjamin.in | Morphic chat UI | Existing frontend ingress | Morphic |
| ai.bchbenjamin.in/_ingress/http/api | Hermes and Personal AI APIs | Outbound Pi relay via Caddy | 127.0.0.1:8642 or 127.0.0.1:8000 |
| ai.bchbenjamin.in/_ingress/http/mcp/mcp | MCP adapter | Outbound Pi relay via Caddy | 127.0.0.1:8765/mcp |

The Personal AI installer leaves ingress configuration independent. The [Render ingress runbook](../../deployment/networking/README.md) documents the fixed relay paths and Caddy's loopback routing. Beeper's API remains private.

## Local Port Allocations (Pi 5)

- 127.0.0.1:8000 — Personal AI API.
- 127.0.0.1:8765/mcp — authenticated Streamable HTTP MCP adapter.
- 127.0.0.1:8642 — Hermes Agent local API.
- 127.0.0.1:18080 — Caddy origin for the Pi connector.
- 127.0.0.1:23373 — Beeper Desktop local REST / MCP API.
- 127.0.0.1:5900 — wayvnc, if enabled and intentionally loopback-bound.
- Tailscale — private node overlay; verify the current assigned address before relying on any previously recorded IP.

## Directionality

- Node agents initiate outbound HTTPS or loopback requests to the Personal AI API and poll for work.
- MCP clients initiate authenticated requests to the MCP adapter.
- The MCP adapter forwards the same scoped bearer token to the Personal AI API.
- Layer 2 calls the AI Gateway's inference routes separately from the reverse relay.
- The Gateway authenticates the connector and forwards requests over its outbound WebSocket. The destination validates the caller's bearer. The Gateway has no stored Personal AI client or execution credential.

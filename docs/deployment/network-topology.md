# Network Topology & Domain Routing

## Domain Layout

| Domain | Role | Ingress Route | Destination |
|---|---|---|---|
| ai.bchbenjamin.in | Layer 1 inference-only gateway | Existing independent deployment | AI Gateway inference service |
| hermes.bchbenjamin.in | Morphic chat UI | Existing frontend ingress | Morphic |
| api.hermes.bchbenjamin.in | Personal AI API | Private reverse proxy / Tailscale ingress | 127.0.0.1:8000 |
| mcp.hermes.bchbenjamin.in | MCP adapter | Private reverse proxy / Tailscale ingress | 127.0.0.1:8765/mcp |

The Personal AI installer does not alter DNS, Cloudflare, Caddy, Nginx or Tailscale Serve configuration. Configure the existing ingress to forward only to the loopback listeners above and enforce TLS. Do not expose node-agent polling ports or Beeper's local API publicly.

## Local Port Allocations (Pi 5)

- 127.0.0.1:8000 — Personal AI API.
- 127.0.0.1:8765/mcp — authenticated Streamable HTTP MCP adapter.
- 127.0.0.1:8642 — Hermes Agent local API.
- 127.0.0.1:23373 — Beeper Desktop local REST / MCP API.
- 127.0.0.1:5900 — wayvnc, if enabled and intentionally loopback-bound.
- Tailscale — private node overlay; verify the current assigned address before relying on any previously recorded IP.

## Directionality

- Node agents initiate outbound HTTPS or loopback requests to the Personal AI API and poll for work.
- MCP clients initiate authenticated requests to the MCP adapter.
- The MCP adapter forwards the same scoped bearer token to the Personal AI API.
- Layer 2 calls the AI Gateway for model inference only.
- The AI Gateway has no route, key or listener for Personal AI nodes, context or control-plane APIs.

# Network Topology & Domain Routing

## Domain Layout

| Domain | Role | Ingress Route | Destination Service |
| :--- | :--- | :--- | :--- |
| `ai.bchbenjamin.in` | Layer 1 AI Gateway | Cloudflare DNS -> External Host | AI Gateway Inference Service |
| `hermes.bchbenjamin.in` | Morphic Chat UI | Tailscale / Reverse Proxy | Morphic Container/Node Process |
| `api.hermes.bchbenjamin.in` | Personal AI API | Tailscale / Reverse Proxy | FastAPI Server (`personal-ai-api`) |
| `mcp.hermes.bchbenjamin.in` | MCP Protocol Adapter | Tailscale / Reverse Proxy | MCP Adapter (`mcp.server`) |

## Local Port Allocations (Pi 5)
- `127.0.0.1:8642`: Hermes Agent Local API Server
- `127.0.0.1:23373`: Beeper Desktop Local REST / MCP API
- `127.0.0.1:5900`: wayvnc VNC Server (bound to local loopback)
- `100.73.46.31`: Tailscale WireGuard mesh address

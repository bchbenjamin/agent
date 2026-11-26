# Hermes public ingress on the existing AI Gateway

The Pi runs the Gateway's outbound WebSocket connector. The Gateway relays only fixed HTTP routes. Caddy binds to loopback at `127.0.0.1:18080` and routes approved methods and paths to Hermes (8642), Personal AI (8000), and the separate MCP adapter (8765). The inference gateway does not own a Personal AI credential or an execution tool. Beeper has no public route.

| Purpose | URL |
| --- | --- |
| Pi connector | `wss://ai.bchbenjamin.in/_ingress/connect/pi` |
| Hermes native inference base | `https://ai.bchbenjamin.in/_ingress/http/api/v1` |
| Hermes native session list | `https://ai.bchbenjamin.in/_ingress/http/api/api/sessions` |
| Personal AI MCP | `https://ai.bchbenjamin.in/_ingress/http/mcp/mcp` |
| Web frontend | `https://hermes.bchbenjamin.in` |

The unused Caddy virtual-host names are internal labels passed by the connector. They do not require DNS records. Do not add custom domains or open router ports. The previous [Cloudflare files and design](cloudflare-alternative.md) remain available for reference. Keep their connector disabled.

## Pi installation

Retrieve only `connector.py`, `ingress_policy.py`, `requirements.txt` and `gateway-ingress.service` from the Gateway repository's `deployment/ingress/` at commit `e3cb02e0d8ab8c6983fb684dee567f77310ba126`. Use authenticated GitHub file access if raw access is unavailable. Install the three runtime files in `~/.local/lib/gateway-ingress/`, and install their dependencies in the dedicated `venv` under that directory. No Gateway application installation is needed.

Install the upstream unit under `~/.config/systemd/user/` and `gateway-ingress-pi.conf` as a drop-in in `gateway-ingress.service.d/`. The drop-in orders the connector after the local Caddy service and skips startup without its credential. The upstream unit sets `INGRESS_NODE=pi`, `INGRESS_GATEWAY=wss://ai.bchbenjamin.in`, and `INGRESS_TOKEN_FILE=%h/.config/personal-ai/ingress/render.token`. Use the existing Render-matched Pi token with mode 0600. Keep the connector and origin services enabled in the lingering user manager.

After startup, a valid downstream Hermes credential must return 200 from the public models route. Missing credentials return 401 and private routes return 404. The serving Gateway returns `503 Ingress disabled` when its effective Pi connector token is absent or too short. A correctly enabled Gateway with no available connector returns `503 Origin unavailable or busy`. A locally active systemd process alone does not confirm a connected peer.

The shared policy forwards Authorization, Content-Type, Origin, MCP session/protocol headers, query parameters, SSE data, HTTP status, and the legacy and native session ID headers. The pinned Gateway implementation omits `x-hermes-session-key`. To support that header end to end, add it to both `REQUEST_HEADERS` and `RESPONSE_HEADERS` in both identical Gateway policy files. Extend Gateway `test_stream_and_headers` to assert the request frame carries it and the relay response echoes it. Preserve the policy parity test, deploy the Gateway fix separately, then refresh the Pi policy from that commit. Use explicit `X-Hermes-Session-Id` for disposable web chat until the session-key path has been verified.

To stop publication without affecting local services, disable and stop only `gateway-ingress.service`. The local Caddy origin and Hermes runtime stay in place.

## Frontend

Set the existing Morphic production project to `HERMES_API_BASE_URL=https://ai.bchbenjamin.in/_ingress/http/api/v1`, `HERMES_API_MODEL=hermes`, and sensitive server-side `HERMES_API_KEY` from the canonical Hermes downstream `API_SERVER_KEY`. Both the connector token and personal admin token are separate. Never expose these secrets to browser code. Use the [native backend contract](../../docs/deployment/hermes-frontend-contract.md) for history and streaming.

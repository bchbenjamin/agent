# Hermes HTTPS ingress

The Pi runs a loopback-only Caddy origin on `127.0.0.1:18080`. Public TLS terminates at an edge relay. The API virtual host routes native Hermes requests to port 8642 and Personal AI control-plane requests to port 8000. The MCP host routes only `/mcp` to port 8765. Beeper is outside the routing table.

Caddy requires a bearer header before contacting a backend. Hermes validates its downstream key, and the Personal AI API and MCP adapter validate their own scoped credentials. The public method/path allowlist excludes node enrollment, node revocation, task approval, task approval listing, context indexing, health and documentation routes, and destructive session operations. Node heartbeat, polling, and result submission still require a node credential. Caddy rewrites only the MCP upstream Host to loopback and preserves Origin so the SDK can enforce its existing DNS rebinding protection.

## Cloudflare account setup

1. Create a dedicated named Cloudflare Tunnel using the existing zone. Configure these two public origin hostnames. Both use an HTTP service at `http://127.0.0.1:18080`.

   | First-level tunnel hostname | HTTP Host Header sent to Caddy |
   | --- | --- |
   | `hermes-api-origin.bchbenjamin.in` | `api.hermes.bchbenjamin.in` |
   | `hermes-mcp-origin.bchbenjamin.in` | `mcp.hermes.bchbenjamin.in` |

   The origin hostnames use Cloudflare-proxied CNAMEs to the tunnel's `<UUID>.cfargotunnel.com` target. Use the same dedicated tunnel for both. Do not add routes for the inference gateway, Beeper, or the Vercel frontend.
2. Install the tunnel's dedicated connector token on the Pi as `~/.config/personal-ai/ingress/cloudflared.token`, mode 0600, using private input. The connector uses outbound HTTP/2 over TCP 7844 and skips startup while the token file is absent. Run this from a private Bash terminal on the Pi:

   ```bash
   umask 077
   read -rsp 'Dedicated Cloudflare Tunnel token: ' tunnel_token
   printf '\n'
   if [ -n "$tunnel_token" ]; then
       printf '%s\n' "$tunnel_token" > "$HOME/.config/personal-ai/ingress/cloudflared.token"
       chmod 0600 "$HOME/.config/personal-ai/ingress/cloudflared.token"
       unset tunnel_token
       systemctl --user start personal-ai-ingress-tunnel.service
   fi
   ```
3. Deploy the Worker defined in `wrangler.toml` from this directory with the owner's authenticated Cloudflare account. The Worker Custom Domains create the two nested DNS records and TLS certificates. Cloudflare Universal SSL for a full DNS zone only covers the apex and first-level names. Do not add CNAME records for the two nested Worker hostnames beforehand. The Worker relays the bearer, request body, SSE stream and MCP headers without following origin redirects or caching the response.

This route uses application bearer authentication. It has no dependency on a Cloudflare Access enrollment flow. If the account cannot create the dedicated named tunnel without payment verification, leave the connector inactive and the two public records absent. Tailscale Serve is a private tailnet option. Funnel can publish a tailnet hostname, but its certificate does not cover these custom domains.

## Pi services

The service templates run without root under the existing lingering user systemd manager. Their executables live at `~/.local/lib/personal-ai/ingress/caddy` and `~/.local/lib/personal-ai/ingress/cloudflared`. Install the service files under `~/.config/systemd/user/` and the Caddyfile at `~/.config/personal-ai/ingress/Caddyfile`. Validate the configuration with `caddy validate --config Caddyfile.hermes --adapter caddyfile` before starting it.

After publishing DNS, test from outside the Pi. Verify TLS, missing and invalid bearer rejection, scoped access, wrong-service bearer rejection, and 404 for private routes. Confirm native Hermes SSE framing and the MCP initialize, tools/list, and list_nodes flow. Keep Authorization and personal query strings out of logs.

## Morphic

Set `HERMES_API_BASE_URL=https://api.hermes.bchbenjamin.in/v1`, `HERMES_API_MODEL=hermes`, and the existing downstream Hermes key as sensitive server-side `HERMES_API_KEY` in the linked Morphic production project. For command-line transfer, read `API_SERVER_KEY` from the Pi's private `~/.hermes-pi/.env` with a dotenv parser and pipe it directly to `vercel env add HERMES_API_KEY production --sensitive`. Verify the linked project before running that command and keep the value out of stdout, command arguments, and shell history. Do not use the inference gateway key or a Personal AI admin or node credential.

## Supplementary research

Register the separate research service as a remote Streamable HTTP MCP server in the canonical Hermes configuration. Use a distinct bearer credential in the private Hermes environment and configure per-server tool selection. Preserve the native `web_search` and `web_extract` tools and expose only supplementary capabilities. The research service needs no access to the Pi filesystem, node token, or inference gateway credentials.

```yaml
mcp_servers:
  shared_research:
    url: https://research.example.org/mcp
    headers:
      Authorization: "Bearer ${RESEARCH_MCP_API_KEY}"
    connect_timeout: 15
    timeout: 120
```

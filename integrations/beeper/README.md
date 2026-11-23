# Beeper Desktop Integration

## Architecture
Beeper Desktop runs as a boot-time systemd service (`beeper.service`) under the user session.
- **Headless Display**: Uses `labwc` on `wayland-0` / Xwayland `:0` (1920x1080 virtual display `NOOP-1`).
- **Local API**: Express API bound to `http://127.0.0.1:23373`.
- **MCP Endpoint**: `http://127.0.0.1:23373/v0/mcp`.
- **Authentication**: OAuth 2.0 with PKCE consent modal in Electron app.

## OAuth Approval Automation
When `hermes mcp login beeper` runs:
1. Hermes requests authorization from `http://127.0.0.1:23373/oauth/authorize`.
2. A POST to `/oauth/authorize/callback` renders an Electron dialog in Beeper.
3. Clicking "Approve" (coordinates 700, 552 on 1920x1080 display) returns the authorization code to Hermes' listener.
4. Hermes exchanges the code for tokens stored in `mcp-tokens/`.

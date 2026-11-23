# Permission Matrix & Credential Management

## Client Permission Profiles

| Client | Permitted Scopes | Default Elevation Required | Revocation Procedure |
| :--- | :--- | :--- | :--- |
| **Morphic Web UI** | `context:read`, `terminal:execute` | Yes for destructive shell | Invalidate client token via `TokenManager.revoke_token()` |
| **Telegram Bot** | `context:read`, `terminal:execute` | Yes for all actions | Invalidate client token in bot environment |
| **Claude Desktop (MCP)** | `context:read`, `nodes:read` | No | Remove client entry in MCP registry |
| **Claude Code (MCP)** | `context:read`, `nodes:read`, `files:read`, `terminal:execute` | Yes for outside-workspace writes | Invalidate CLI plugin key |
| **Node Agents** | `nodes:read`, `deploy:execute` | Yes for package installation | Rotate node mutual TLS secret |

## Credential Revocation Runbook
To immediately revoke any client token:
1. Identify the token string or client ID.
2. In the Personal AI API console or admin script:
   ```python
   from control_plane.authentication.tokens import TokenManager
   tm = TokenManager()
   tm.revoke_token("pai_morphic_...")
   ```
3. The token hash is deactivated immediately in memory and persisted storage.

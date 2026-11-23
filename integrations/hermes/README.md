# Hermes Agent Integration

## Architecture
Hermes Agent runs as a persistent service on worker nodes (e.g. Raspberry Pi 5).
- Upstream: Routes inference queries to Layer 1 AI Gateway (`https://ai.bchbenjamin.in/codex/v1`).
- Downstream: Binds OpenAI-compatible API on `127.0.0.1:8642`.
- MCP Tools:
  - `beeper`: Local Beeper Desktop API integration on port 23373.
  - `computer-use-linux`: Wayland desktop control tool.
  - `simular_box`: Remote compute sandbox.

## Deployment
1. Copy `config.template.yaml` to `$HERMES_HOME/config.yaml`.
2. Copy `env.template` to `$HERMES_HOME/.env` and populate keys (set mode `0600`).
3. Install user systemd service:
   ```bash
   hermes gateway install --force --start-now --start-on-login
   ```

# Hermes Agent Integration

Hermes is the agent runtime and context/memory layer on the Raspberry Pi 5. It routes inference to the isolated Layer 1 AI Gateway and uses local MCP integrations for device and messaging operations.

## Connections

- **AI Gateway**: `https://ai.bchbenjamin.in/codex/v1` for inference only. It has no device or personal-context permissions.
- **Personal AI MCP**: `https://mcp.hermes.bchbenjamin.in/mcp` (Streamable HTTP). Configure a dedicated API-issued `PAI_API_TOKEN` with only the scopes Hermes needs.
- **Beeper**: `http://127.0.0.1:23373/v0/mcp`, OAuth-protected local MCP.
- **Simular Box**: `https://mcp.box.simular.ai/mcp`, authenticated remote execution sandbox.
- **Pi desktop control**: preserve Hermes native Computer Use with native Wayland enabled. The upstream computer-use-linux stdio MCP can also be registered locally using command computer-use-linux and args ["mcp"]; review the resulting tool list to avoid duplicate overlapping controllers.

## Configuration

1. Copy `config.template.yaml` to `$HERMES_HOME/config.yaml`.
2. Copy `env.template` to `$HERMES_HOME/.env` and populate the AI Gateway key, a dedicated Personal AI client token, and the Box key if used.
3. Set the env file to mode `0600`.
4. Keep the Beeper OAuth consent flow local to the Pi.
5. Restart the Hermes user service and verify each MCP connection independently.

Do not reuse the AI Gateway key as a Personal AI API credential. Client credentials are separate and revocable.

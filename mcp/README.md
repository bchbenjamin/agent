# MCP protocol adapter

The Python import name `mcp` is owned by the official Model Context Protocol SDK. To avoid shadowing that SDK at runtime, the project's executable adapter package is `pai_mcp/`.

- `pai_mcp/server.py`: official Python MCP SDK server (stdio and authenticated Streamable HTTP).
- `pai_mcp/adapter.py`: thin API client; it does not implement authorization or execute commands.
- All authorization is delegated to `api.hermes.bchbenjamin.in`.

For external chatbot clients, see [External brain MCP](../docs/deployment/external-brain-mcp.md). The adapter now exposes shared context read/write tools, client scope inspection, and optional read-only Beeper and Box federation. External-brain credentials are intentionally separate from Hermes and admin credentials.

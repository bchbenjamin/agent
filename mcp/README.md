# MCP protocol adapter

The Python import name `mcp` is owned by the official Model Context Protocol SDK. To avoid shadowing that SDK at runtime, the project's executable adapter package is `pai_mcp/`.

- `pai_mcp/server.py`: official Python MCP SDK server (stdio and authenticated Streamable HTTP).
- `pai_mcp/adapter.py`: thin API client; it does not implement authorization or execute commands.
- All authorization is delegated to `api.hermes.bchbenjamin.in`.

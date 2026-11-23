# Simular Box MCP Integration

## Purpose
Simular Box provides remote containerized execution for tasks requiring an external x86_64 Linux desktop or cloud browser sandbox.

## Configuration
- Endpoint: `https://mcp.box.simular.ai/mcp`
- Transport: Streamable HTTP / Server-Sent Events (SSE)
- Credential: `MCP_BOX_API_KEY` (configured in node private `.env`)
- Trust: `untrusted` (ensures human approval prompts for write/destructive actions)

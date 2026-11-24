# computer-use-linux Integration

## Overview

The upstream @agent-sh/computer-use-linux project provides a local Linux desktop observation/control CLI and stdio MCP server. It is not replaced by a custom Personal AI server.

- Backend: Pi Wayland desktop and Xwayland.
- Tools: accessibility inspection, screenshots, window targeting and input injection.
- Security: the MCP server can mutate visible application state; keep the server local, set trust to untrusted and review mutating actions.
- The Personal AI API does not proxy desktop-control calls. Hermes connects to the local stdio MCP directly.

## Install on the Pi

Install the upstream npm package and Hermes skill:

    npm install -g @agent-sh/computer-use-linux
    hermes skills tap add agent-sh/computer-use-linux
    hermes skills install agent-sh/computer-use-linux/computer-use-linux

Register the local stdio MCP:

    hermes mcp add computer-use-linux --command computer-use-linux --args mcp
    hermes mcp test computer-use-linux
    hermes mcp configure computer-use-linux

The generated Hermes MCP configuration should use command: computer-use-linux and args: ["mcp"]. Keep it local; do not expose it as an unauthenticated network service.

## Verification

    computer-use-linux doctor
    hermes skills inspect agent-sh/computer-use-linux/computer-use-linux
    hermes chat --toolsets mcp-computer-use-linux -q "List the current desktop windows."

The Pi's existing Hermes native Wayland Computer Use configuration is preserved. Review tool discovery after adding this MCP and avoid enabling duplicate overlapping desktop controllers.

## References

- Upstream repository: https://github.com/agent-sh/computer-use-linux
- Upstream npm documentation: https://github.com/agent-sh/computer-use-linux/blob/main/npm/README.md

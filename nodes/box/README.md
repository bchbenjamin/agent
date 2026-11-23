# Simular Box Node Specification

## Role
Simular Box (`box`) serves as an auxiliary remote sandbox.
- It is accessed via the Simular Box Streamable HTTP MCP endpoint (`https://mcp.box.simular.ai/mcp`).
- It enables browser operations and x86_64 software evaluation without placing compute load on the Raspberry Pi 5.
- Because the Box filesystem is ephemeral, it must **never** be used to store personal databases, Beeper profiles, or persistent Hermes memory.

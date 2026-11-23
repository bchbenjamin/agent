# ADR 0002: Model Context Protocol (MCP) as Protocol Adapter

## Context
External AI clients (e.g. Claude Desktop, external IDE agents) need to interact with the personal infrastructure. Implementing custom authentication and permission checks directly inside every MCP server risks code drift and unauthorized access.

## Decision
Treat MCP strictly as a protocol adapter over the Personal AI API (`api.hermes.bchbenjamin.in`).
- The MCP server exposes tools and resources defined in the API schema.
- Every tool call converts into an authenticated REST/RPC request to the Personal AI API using the client's scoped token.
- Central authorization policies and audit logs handle execution and auditing.

## Consequences
- Single source of truth for authorization policies.
- Uniform audit trail across web UI, Telegram bot, and MCP clients.
- Prevents unauthenticated bypasses.

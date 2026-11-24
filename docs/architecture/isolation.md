# Architectural Isolation: Layer 1 vs Layer 2

## Layer 1: Independent AI Gateway

- Domain: https://ai.bchbenjamin.in
- Responsibility: model inference, rate limiting, provider routing and token accounting.
- Outbound to external model providers.
- Inbound completion requests only.
- No route, credentials or permission to access Personal AI nodes, local files, databases, messages or memory.
- Separate repository and deployment lifecycle.

## Layer 2: Personal AI Infrastructure

- hermes.bchbenjamin.in — Morphic UI.
- api.hermes.bchbenjamin.in — Personal AI API and control plane.
- mcp.hermes.bchbenjamin.in — authenticated MCP protocol adapter.
- Hermes supplies agent runtime and shared context/memory.
- The API owns client scopes, task routing, node registry, approvals and audit; its SQLite database is owned by the dedicated pai-api account.
- MCP runs as pai-mcp and the outbound node daemon as pai-agent; neither can read the API database. Task subprocesses run as bchbenjamin through a narrow helper.
- Pi 5 runs the API, MCP adapter and unprivileged node agent; Beeper and Hermes Computer Use remain local.
- Simular Box is an auxiliary node; Redmi is staged.

Directionality: Layer 2 calls Layer 1 for inference. Layer 1 cannot query, initiate connections to or access Layer 2.

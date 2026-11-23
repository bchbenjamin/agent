# Architectural Isolation: Layer 1 vs Layer 2

## Principle of Separation
The personal AI infrastructure enforces strict isolation between Layer 1 (AI Gateway) and Layer 2 (Personal AI Infrastructure).

### Layer 1: Independent AI Gateway
- **Domain**: `https://ai.bchbenjamin.in`
- **Responsibility**: Model inference, rate limiting, provider routing, token accounting.
- **Access Boundary**:
  - Outbound to external LLM providers (Anthropic, OpenAI, custom).
  - Inbound only for completion queries (`POST /codex/v1/chat/completions`).
  - No access to local file systems, nodes, personal databases, or memory.
  - Independent credentials, configuration, and repository.

### Layer 2: Personal AI Infrastructure
- **Domains**:
  - `https://hermes.bchbenjamin.in` (Morphic UI)
  - `https://api.hermes.bchbenjamin.in` (Personal AI API)
  - `https://mcp.hermes.bchbenjamin.in` (MCP protocol adapter)
- **Responsibility**: Context retrieval, node management, service orchestration, messaging, task execution.
- **Directionality**: Layer 2 queries Layer 1 for model inference. Layer 1 can NEVER query or access Layer 2.

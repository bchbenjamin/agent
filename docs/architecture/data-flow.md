# End-to-End Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Client
    participant Frontend as Morphic / Telegram
    participant MCP as MCP Adapter (mcp.hermes.bchbenjamin.in)
    participant API as Personal AI API (api.hermes.bchbenjamin.in)
    participant Agent as Hermes / Node Agent
    participant Gateway as Layer 1 AI Gateway (ai.bchbenjamin.in)
    participant Edge as Edge Services (Beeper / Display)

    Note over User,Gateway: Scenario 1: External Client Task via MCP
    User->>MCP: Call tool `get_node_status` with Bearer token
    MCP->>API: Forward authenticated request
    API->>API: Verify token & scope (`nodes:read`)
    API->>Agent: Query node status via private overlay
    Agent-->>API: Return hardware & service status
    API-->>MCP: Formatted status payload
    MCP-->>User: MCP tool result

    Note over User,Gateway: Scenario 2: Autonomous Agent Inference
    Agent->>Gateway: POST /codex/v1/chat/completions (Outbound)
    Gateway-->>Agent: LLM completion with tool call
    Agent->>Edge: Execute local tool (e.g. Beeper search)
    Edge-->>Agent: Tool result
    Agent->>Gateway: Send tool result for final response
    Gateway-->>Agent: Natural language summary
```

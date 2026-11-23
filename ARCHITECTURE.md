# Architecture Specification

## 1. Architectural Philosophy

The Personal AI Infrastructure is designed around two principles:
1. **Zero-Trust Separation of Model Inference from Personal State**:
   External AI models and inference providers have access only to explicitly supplied prompt context. They never possess direct access to storage, network devices, personal message history, or node management.
2. **Unified Control Plane with Edge Execution**:
   Control logic, authentication, and task dispatching are centralized in the Personal AI API, while actual execution occurs on dedicated edge nodes (Raspberry Pi 5, mobile nodes, remote sandboxes).

---

## 2. The Two Isolated Layers

```text
+-----------------------------------------------------------------------------------+
|                        LAYER 1: AI GATEWAY (INFERENCE ONLY)                       |
|                             https://ai.bchbenjamin.in                             |
|                                                                                   |
|  - Independent inference router and model provider gateway.                       |
|  - Endpoints: /codex/v1/chat/completions, /codex/v1/models                        |
|  - Credential: AI_GATEWAY_API_KEY (Bearer token for completions only)              |
|  - INGRESS ONLY FROM AUTHORIZED CLIENTS (Hermes, Claude Code, etc.)               |
|  - ZERO EGRESS INTO PERSONAL CONTEXT, NODES, OR INFRASTRUCTURE.                   |
+-----------------------------------------------------------------------------------+
                                        ^
                                        | POST /codex/v1/chat/completions (Outbound)
                                        | [Model inference query and completion]
+-----------------------------------------------------------------------------------+
|                     LAYER 2: PERSONAL AI INFRASTRUCTURE                           |
|                                                                                   |
|   +---------------------------------------------------------------------------+   |
|   | Domain Entrypoints:                                                       |   |
|   |  - https://hermes.bchbenjamin.in     -> Morphic Frontend                  |   |
|   |  - https://api.hermes.bchbenjamin.in -> Personal AI API / Control Plane   |   |
|   |  - https://mcp.hermes.bchbenjamin.in -> Protocol Adapter (MCP Clients)    |   |
|   +---------------------------------------------------------------------------+   |
|                                        |                                          |
|                                        v                                          |
|   +---------------------------------------------------------------------------+   |
|   | Control Plane & Personal AI API:                                          |   |
|   |  - Authenticates clients (Morphic, Telegram, external MCP clients)        |   |
|   |  - Evaluates authorization scopes (e.g., context:read, terminal:execute)  |   |
|   |  - Manages Node Registry and dispatches work via Task Router              |   |
|   |  - Maintains immutable structured Audit Logs                              |   |
|   +---------------------------------------------------------------------------+   |
|                                        |                                          |
|                     WireGuard / Tailnet Private Overlay                           |
|                                        |                                          |
|         +------------------------------+------------------------------+           |
|         |                                                             |           |
|         v                                                             v           |
|   +--------------------------+                                  +-------------+   |
|   | Node: Raspberry Pi 5     |                                  | Node: Box   |   |
|   |  - Node Agent Daemon     |                                  |  - Simular  |   |
|   |  - Hermes Agent Runtime  |                                  |    Worker   |   |
|   |  - Beeper Desktop API    |                                  |  - Compute  |   |
|   |  - computer-use-linux    |                                  |    Sandbox  |   |
|   |  - SSD /mnt/pi_data      |                                  +-------------+   |
|   +--------------------------+                                                    |
+-----------------------------------------------------------------------------------+
```

---

## 3. Protocol Adapters (MCP)

Model Context Protocol (MCP) clients (such as Claude Desktop, external IDE agents, or Claude Code) connect via `https://mcp.hermes.bchbenjamin.in`.

**Critical Design Rule**: MCP is strictly a **protocol adapter** over the Personal AI API.
- The MCP server does not implement custom authorization logic, file access, or node communication.
- Every MCP tool call is mapped directly to an authenticated REST/RPC invocation against `https://api.hermes.bchbenjamin.in`.
- Client requests present scoped bearer tokens; unauthenticated operations are rejected before reaching execution adapters.

---

## 4. Node Agent Execution Model

Each managed node runs an unprivileged `node-agent` daemon.
1. **Unprivileged by Default**:
   The agent runs under a standard non-root user (e.g. `bchbenjamin` on Pi 5).
2. **Narrowly Scoped Privileged Helper**:
   System-level modifications (such as mounting storage or restarting systemd units) are restricted to pre-validated commands with specific parameter filters.
3. **Resilience & Automatic Reconnection**:
   Node agents maintain an outbound TLS connection over the private tailnet to the Control Plane. If a node loses internet connectivity or reboots, it re-registers automatically upon reconnecting.
4. **Cloud Portability**:
   The Control Plane and Personal AI API are designed to run identically on the Raspberry Pi 5 or inside a hardened cloud VM (e.g. Oracle Cloud Infrastructure). The edge nodes remain identical in either topology.

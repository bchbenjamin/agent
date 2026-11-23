# Audit Logging Schema & Policy

## Purpose
All sensitive operations routed through the Personal AI API or executed on managed nodes emit immutable, structured audit records.

## Audit Record Format
```json
{
  "event_id": "evt_7e2a1b9c3f4d5e6a",
  "timestamp": "2026-11-23T08:00:00Z",
  "client_id": "claude-code",
  "user_identity": "bchbenjamin",
  "target_node": "pi5",
  "operation": "terminal:execute",
  "target_resource": "/home/bchbenjamin/Projects",
  "approval_status": "approved",
  "result": "success",
  "client_ip": "100.73.46.31"
}
```

## Security Guarantees
1. **Zero Secret Leakage**: Tokens, private chat data, passwords, and environment keys are strictly redacted before emission.
2. **Cryptographic Chaining**: Each record's `event_id` is derived from the SHA-256 hash of the previous record plus current event parameters, preventing retro-active alteration.

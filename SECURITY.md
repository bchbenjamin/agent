# Security Model & Policy

## 1. Threat Model & Boundaries

The security posture assumes that:
- External model inference endpoints may be subject to prompt injection or malicious input.
- Local nodes contain personal communication history, encrypted credentials, and private documents.
- Physical devices may undergo unexpected network reconfigurations.

### Mitigations
1. **Strict Layer Isolation**:
   The AI Gateway has no network path into local nodes. It exposes only completion APIs.
2. **Permission Scoping**:
   All Personal AI API interactions are governed by least-privilege tokens.
3. **Approval Gates for Destructive Actions**:
   Disk repartitioning, file deletion, and privileged package installations require interactive two-factor approval.
4. **Zero Secrets in Repository**:
   No cryptographic keys, tokens, or environment files are ever stored in Git.

---

## 2. Permission Scopes

The Personal AI API enforces granular scopes:

| Scope | Category | Description | Requires Elevation |
| :--- | :--- | :--- | :--- |
| `context:read` | Read | Read personal notes, preferences, and indexed documentation | No |
| `nodes:read` | Read | Query node health, status, CPU/RAM, and uptime | No |
| `files:read` | Read | Read files within authorized directory sandboxes | No |
| `files:write` | Write | Write or modify files in user workspaces | Yes (if outside workspace) |
| `terminal:execute` | Execute | Execute command line processes in user sandbox | Yes (if non-whitelisted) |
| `services:manage` | Admin | Restart, stop, or inspect system services | Yes |
| `deploy:execute` | Admin | Trigger node upgrades, package installations | Yes |
| `nodes:admin` | Admin | Add, deprovision, or reconfigure node topology | Yes |

---

## 3. Credential Segregation

Independent cryptographic credentials are used across the infrastructure:

```text
1. AI Gateway Client Key       -> Authenticates Hermes/Claude to https://ai.bchbenjamin.in
2. Personal AI API Token       -> Authenticates clients (Morphic, Telegram) to Personal AI API
3. Node Agent Secret           -> Mutual authentication between Node Agent and Control Plane
4. Simular Box API Key         -> Authenticates Simular Box MCP worker
5. Beeper Local OAuth          -> Local token stored in private SQLite/JSON, never shared
```

---

## 4. Audit Logging Standard

Every sensitive request processed by the Control Plane emits an immutable audit event:
```json
{
  "event_id": "evt_9f3a8b2c1d0e",
  "timestamp": "2026-11-23T07:55:00Z",
  "client_id": "morphic-web-client",
  "user_identity": "bchbenjamin",
  "target_node": "pi5",
  "operation": "services:manage.restart",
  "target_resource": "beeper.service",
  "approval_status": "approved_by_user",
  "result": "success",
  "client_ip": "100.73.46.31"
}
```
Audit logs are stored in a local append-only log with cryptographic hash-chaining.

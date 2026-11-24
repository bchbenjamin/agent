# Security Model & Policy

## 1. Threat model and boundaries

The design assumes external inference endpoints may return prompt-injected content and local nodes contain personal messages, credentials and private files.

### Mitigations

1. **Strict layer isolation**: ai.bchbenjamin.in is inference-only. It has no Personal AI API credentials, node routes or access to personal context.
2. **Per-client authorization**: every API and MCP client uses an independent bearer token with explicit scopes.
3. **Account separation**: the API database belongs to pai-api, MCP runs as pai-mcp, and the node daemon runs as pai-agent. Task processes run as bchbenjamin through a fixed helper, not as root.
4. **Outbound node protocol**: nodes authenticate to the API and poll for work; no public inbound node-agent port is opened.
5. **Narrow privileged helper**: the root-owned helper permits only an allowlisted systemd restart or execution as the normal bchbenjamin user. It does not accept arbitrary root commands.
6. **Approval gates**: explicit shell, disk mutation, recursive deletion, package/system changes and service restarts are held until a separate client with tasks:approve approves the task.
7. **Secret hygiene**: no active tokens, environment files, databases or keyrings belong in Git. The node credential is stored under /var/lib/pai-agent; the admin token is root-only at /etc/personal-ai/admin-token; the API database is inaccessible to task processes running as bchbenjamin.
8. **Audit**: sensitive operations and task outcomes are recorded in a persistent SHA-256 hash chain. Audit details deliberately exclude command output and private content.

## 2. Permission scopes

| Scope | Category | Description | Approval |
|---|---|---|---|
| context:read | Read | Search explicitly indexed personal context | No |
| context:write | Write | Add documents through the context index API | Separate indexer token |
| nodes:read | Read | List nodes, inspect status, request service status | No |
| files:read | Read | Reserved for future structured file tools | No |
| files:write | Write | Reserved for future structured file tools | Depends on operation |
| terminal:execute | Execute | Run argv tasks in the user's unprivileged context | Sensitive commands require approval |
| services:manage | Admin | Request allowlisted service restart/status | Restart requires approval |
| deploy:execute | Admin | Reserved for deployment operations | Not yet exposed |
| tasks:approve | Approval | List and approve pending high-impact tasks | Explicit separate action |
| nodes:admin | Admin | Administrative override for scopes and node management | Owner-only |

The current task API exposes argv execution, explicitly approved shell execution, service status and allowlisted service restart. It does not expose an unrestricted root shell.

## 3. Credential segregation

1. AI Gateway key — authenticates Hermes to the independent inference service.
2. Personal AI client token — authenticates Morphic, Hermes or each MCP client.
3. Node token — authenticates the pai-agent daemon to the Personal AI API.
4. Node enrollment secret — one-time bootstrap credential, removed from the API service environment after initial enrollment.
5. Context-index token — grants context:write only; it cannot read indexed content or submit tasks.
6. Bootstrap admin token — stored root-only at /etc/personal-ai/admin-token.
7. Simular Box key — authenticates the Box MCP client.
8. Beeper OAuth — remains local to Beeper/Hermes.

Tokens are random and only their SHA-256 hashes are persisted. The plaintext client or node token is returned only at issuance/enrollment.

## 4. Audit logging

Audit events include event ID, timestamp, client/user, node, operation, resource, approval state, result, client IP, details, previous hash and event hash. The hash covers the event ID and canonical event body plus the previous event hash.

Verify the chain with:

    sudo -u pai-api env PAI_DB_PATH=/mnt/pi_data/personal-ai/pai.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli verify-audit

The chain is tamper-evident, not an immutable or signed ledger. Protect the database with filesystem permissions and encrypted off-device backups. Never store bearer tokens, passwords, command output, message bodies or private file contents in audit details.

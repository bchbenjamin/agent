# Threat Model & Security Posture

## Assets
- Beeper message history and attachments.
- Personal files and the data-only SSD at /mnt/pi_data.
- Node execution and device-control permissions.
- AI Gateway and Personal AI credentials.

## Boundaries
- The AI Gateway is inference-only and has no route or credential for Layer 2.
- Personal AI API owns client authentication, scopes, approvals, task state and audit.
- Nodes make outbound authenticated requests; no inbound node listener is required.
- MCP is an adapter and passes the client bearer token to the API.

## Mitigations
- Independent per-client API credentials and per-node bearer credentials.
- Hash-only token persistence and revocation.
- Dedicated pai-api database owner, pai-mcp adapter account and pai-agent daemon account. The task identity cannot read the API database or node token.
- Unprivileged node agent; no general root shell.
- argv execution by default; explicit shell, destructive commands and service restarts require approval.
- A root-owned helper only accepts allowlisted systemd actions.
- Persistent hash-chained audit records.
- Context indexing is opt-in and restricted to configured roots; secret/config directories and common credential files are excluded.
- Public MCP requests without a valid API-issued bearer token are rejected.

## Residual risks
A client with terminal:execute can still read or modify any resource available to the node's Unix user. Prompt injection can request actions within that granted authority. Keep client scopes narrow, use approval for sensitive operations, review audit records, and do not run the agent as root. The hash chain is tamper-evident, not a substitute for protected/encrypted backups.

# Audit Logging Schema & Policy

Sensitive API operations, task submission, approval and node execution results are recorded in SQLite's append-only audit table.

Each event includes the client/user identity, target node, operation, resource, approval status, result, client IP, details, previous event hash and current SHA-256 event hash. Each event hash covers the previous hash and canonical JSON event body.

Verify the chain:

    python -m personal_ai_api.cli verify-audit

A valid chain detects modification, deletion or reordering of existing records. It does not protect against an attacker who can rewrite the entire database and recompute the chain; use filesystem permissions and encrypted off-device backups as additional controls. Never put tokens, passwords, Beeper messages or private file contents in audit details.

# Permission Matrix & Credential Management

## Scopes

| Scope | Capability | Notes |
|---|---|---|
| context:read | Search explicitly indexed personal context | No filesystem crawling on API request |
| context:write | Add documents to the context index through the API | Separate indexer token; no query permission |
| nodes:read | List nodes, inspect node status, submit service status task | Requires registered node |
| files:read | Reserved for future structured file tools | Current broad file access is through scoped terminal execution |
| files:write | Reserved for future structured file tools | User-workspace writes are possible through terminal execution |
| terminal:execute | Submit argv or shell tasks to a node | Shell and sensitive commands require approval |
| services:manage | Submit service management tasks | Service restart requires approval and helper allowlist |
| deploy:execute | Deployment task scope | Not yet exposed as a remote task operation |
| tasks:approve | List and approve tasks awaiting explicit approval | Separate from task submission |
| nodes:admin | Administrative override for scopes and node management | Reserve for owner/admin clients |

## Client separation

Issue one token per client. Do not reuse the AI Gateway key as a Personal AI API token. Production token administration runs as the pai-api system account because the database is not readable by bchbenjamin or node-agent processes.

Example context-indexer token:

    sudo -u pai-api env PAI_DB_PATH=/var/lib/pai-api/control-plane.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli issue-token --client-id context-indexer --client-type indexer --user owner --scopes context:write

Save this token mode 0600 at ~/.config/personal-ai/context-index-token. It can only add documents; it cannot search context, submit tasks or administer nodes.

Example Hermes token:

    sudo -u pai-api env PAI_DB_PATH=/var/lib/pai-api/control-plane.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli issue-token --client-id hermes-agent --client-type hermes --user owner --scopes context:read,nodes:read,files:read,terminal:execute,services:manage

Example Morphic token (includes approval capability):

    sudo -u pai-api env PAI_DB_PATH=/var/lib/pai-api/control-plane.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli issue-token --client-id morphic-web --client-type morphic --user owner --scopes context:read,nodes:read,files:read,terminal:execute,services:manage,tasks:approve

Revoke a token or all credentials for a client (run as pai-api):

    sudo -u pai-api env PAI_DB_PATH=/var/lib/pai-api/control-plane.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli revoke-token --token '<token>'
    sudo -u pai-api env PAI_DB_PATH=/var/lib/pai-api/control-plane.sqlite3 /opt/personal-ai/.venv/bin/python -m personal_ai_api.cli revoke-client --client-id morphic-web

Only token hashes are persisted. Plaintext client/node tokens are returned once. The bootstrap admin token is root-only at /etc/personal-ai/admin-token.

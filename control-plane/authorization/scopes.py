"""Authorization policies and scope evaluation."""
from typing import Set, List

# Standard permission scopes
SCOPE_CONTEXT_READ = "context:read"
SCOPE_NODES_READ = "nodes:read"
SCOPE_FILES_READ = "files:read"
SCOPE_FILES_WRITE = "files:write"
SCOPE_TERMINAL_EXECUTE = "terminal:execute"
SCOPE_SERVICES_MANAGE = "services:manage"
SCOPE_DEPLOY_EXECUTE = "deploy:execute"
SCOPE_NODES_ADMIN = "nodes:admin"

ALL_SCOPES: Set[str] = {
    SCOPE_CONTEXT_READ,
    SCOPE_NODES_READ,
    SCOPE_FILES_READ,
    SCOPE_FILES_WRITE,
    SCOPE_TERMINAL_EXECUTE,
    SCOPE_SERVICES_MANAGE,
    SCOPE_DEPLOY_EXECUTE,
    SCOPE_NODES_ADMIN,
}

DESTRUCTIVE_OPERATIONS: List[str] = [
    "storage:format",
    "storage:wipe",
    "services:stop",
    "services:disable",
    "system:reboot",
    "system:shutdown",
    "deploy:rollback",
]

class ScopeValidator:
    """Enforces fine-grained permission scopes and approval policies."""

    @staticmethod
    def has_scope(granted_scopes: Set[str], required_scope: str) -> bool:
        if SCOPE_NODES_ADMIN in granted_scopes:
            return True
        return required_scope in granted_scopes

    @staticmethod
    def requires_explicit_approval(operation: str) -> bool:
        return any(operation.startswith(prefix) for prefix in DESTRUCTIVE_OPERATIONS)

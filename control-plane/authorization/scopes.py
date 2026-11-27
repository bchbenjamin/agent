"""Central authorization scope catalog and operation policy."""

SCOPE_CONTEXT_READ = "context:read"
SCOPE_CONTEXT_WRITE = "context:write"
SCOPE_NODES_READ = "nodes:read"
SCOPE_FILES_READ = "files:read"
SCOPE_FILES_WRITE = "files:write"
SCOPE_TERMINAL_EXECUTE = "terminal:execute"
SCOPE_SERVICES_MANAGE = "services:manage"
SCOPE_DEPLOY_EXECUTE = "deploy:execute"
SCOPE_NODES_ADMIN = "nodes:admin"
SCOPE_TASKS_APPROVE = "tasks:approve"

# External reasoning clients may request work, but must never administer nodes
# or resolve the approval gate. Enforce this at token issuance and validation.
EXTERNAL_BRAIN_FORBIDDEN_SCOPES = {SCOPE_NODES_ADMIN, SCOPE_TASKS_APPROVE}

ALL_SCOPES = {
    SCOPE_CONTEXT_READ,
    SCOPE_CONTEXT_WRITE,
    SCOPE_NODES_READ,
    SCOPE_FILES_READ,
    SCOPE_FILES_WRITE,
    SCOPE_TERMINAL_EXECUTE,
    SCOPE_SERVICES_MANAGE,
    SCOPE_DEPLOY_EXECUTE,
    SCOPE_NODES_ADMIN,
    SCOPE_TASKS_APPROVE,
    "box:read",
    "beeper:read",
}
ADMIN_SCOPES = set(ALL_SCOPES)

DESTRUCTIVE_OPERATIONS = {
    "shell",
    "storage:format",
    "storage:wipe",
    "services:stop",
    "services:disable",
    "services:restart",
    "service_restart",
    "system:reboot",
    "system:shutdown",
    "deploy:rollback",
    "package:install",
    "files:delete",
}

SENSITIVE_EXECUTABLES = {
    "wipefs",
    "mkfs",
    "mkfs.ext4",
    "mkfs.vfat",
    "fdisk",
    "parted",
    "sfdisk",
    "rm",
    "shred",
    "truncate",
    "mount",
    "umount",
    "reboot",
    "shutdown",
    "poweroff",
    "halt",
    "apt",
    "apt-get",
    "dpkg",
    "snap",
    "flatpak",
    "pip",
    "pip3",
    "npm",
    "yarn",
    "pnpm",
}


class ScopeValidator:
    @staticmethod
    def has_scope(granted_scopes: set[str], required_scope: str) -> bool:
        return SCOPE_NODES_ADMIN in granted_scopes or required_scope in granted_scopes

    @staticmethod
    def requires_explicit_approval(operation: str) -> bool:
        op = operation.strip().lower()
        return op in DESTRUCTIVE_OPERATIONS or any(
            op.startswith(x + ":") for x in DESTRUCTIVE_OPERATIONS
        )

    @staticmethod
    def requires_payload_approval(operation: str, payload: dict) -> bool:
        if operation != "exec":
            return False
        argv = payload.get("argv", [])
        if isinstance(argv, str):
            import shlex

            try:
                argv = shlex.split(argv)
            except ValueError:
                return True
        if not isinstance(argv, list) or not argv:
            return False
        executable = str(argv[0]).rsplit("/", 1)[-1]
        if executable in SENSITIVE_EXECUTABLES:
            return True
        if executable in {
            "bash",
            "sh",
            "zsh",
            "dash",
            "fish",
            "python",
            "python3",
            "perl",
            "ruby",
            "node",
        } and any(x in argv for x in ("-c", "-e", "-r")):
            return True
        if executable == "systemctl" and any(
            x in argv
            for x in ("start", "stop", "restart", "reload", "enable", "disable")
        ):
            return True
        if executable == "find" and any(
            x in argv for x in ("-delete", "-exec", "-execdir")
        ):
            return True
        if executable == "dd" and any(str(x).startswith("of=/dev/") for x in argv):
            return True
        if executable in {"chmod", "chown"} and "-R" in argv:
            return True
        if executable == "git" and any(
            x in argv for x in ("push", "clean", "reset", "checkout")
        ):
            return True
        return False

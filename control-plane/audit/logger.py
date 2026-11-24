"""Persistent tamper-evident audit log facade."""

from control_plane.storage import SQLiteStore, get_store


class AuditLogger:
    def __init__(self, log_path=None, store: SQLiteStore | None = None):
        self.store = store or get_store()
        # log_path is retained for backwards compatibility; DB is canonical.

    def log(
        self,
        client_id,
        user_identity,
        target_node,
        operation,
        target_resource,
        approval_status,
        result,
        client_ip=None,
        details=None,
    ):
        return self.store.append_audit(
            {
                "client_id": client_id,
                "user_identity": user_identity,
                "target_node": target_node,
                "operation": operation,
                "target_resource": target_resource,
                "approval_status": approval_status,
                "result": result,
                "client_ip": client_ip,
                "details": details or {},
            }
        )

    def get_recent(self, count=50):
        return self.store.recent_audit(count)

    def verify_chain(self):
        return self.store.verify_audit_chain()

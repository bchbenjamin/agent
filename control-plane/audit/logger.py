"""Immutable audit logging for personal infrastructure operations."""
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
from ..api.schema import AuditRecord

class AuditLogger:
    """Maintains an append-only, tamper-evident log of all sensitive operations."""

    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path
        self._records: List[AuditRecord] = []
        self._last_hash = "0000000000000000000000000000000000000000000000000000000000000000"

    def log(
        self,
        client_id: str,
        user_identity: str,
        target_node: str,
        operation: str,
        target_resource: str,
        approval_status: str,
        result: str,
        client_ip: Optional[str] = None,
    ) -> AuditRecord:
        timestamp = datetime.now(timezone.utc).isoformat()
        raw_id_input = f"{self._last_hash}:{timestamp}:{client_id}:{operation}:{target_resource}"
        event_id = "evt_" + hashlib.sha256(raw_id_input.encode("utf-8")).hexdigest()[:16]
        self._last_hash = hashlib.sha256(raw_id_input.encode("utf-8")).hexdigest()

        record = AuditRecord(
            event_id=event_id,
            timestamp=timestamp,
            client_id=client_id,
            user_identity=user_identity,
            target_node=target_node,
            operation=operation,
            target_resource=target_resource,
            approval_status=approval_status,
            result=result,
            client_ip=client_ip,
        )

        self._records.append(record)

        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.__dict__) + "\n")

        return record

    def get_recent(self, count: int = 50) -> List[AuditRecord]:
        return self._records[-count:]

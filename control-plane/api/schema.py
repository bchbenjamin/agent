"""Control plane schema definitions."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

@dataclass
class NodeRegistration:
    node_id: str
    hostname: str
    architecture: str
    ram_mb: int
    tier: str
    capabilities: List[str]
    tailscale_ip: Optional[str] = None
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class TaskRequest:
    task_id: str
    target_node: str
    operation: str
    payload: Dict[str, Any]
    required_scope: str
    client_id: str
    user_identity: str
    requires_approval: bool = False
    approved: bool = False

@dataclass
class AuditRecord:
    event_id: str
    timestamp: str
    client_id: str
    user_identity: str
    target_node: str
    operation: str
    target_resource: str
    approval_status: str
    result: str
    client_ip: Optional[str] = None

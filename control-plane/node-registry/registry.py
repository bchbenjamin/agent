"""Node Registry maintaining state of all managed nodes."""
from typing import Dict, List, Optional
from datetime import datetime, timezone
from ..api.schema import NodeRegistration

class NodeRegistry:
    """Central registry tracking active, standby, and edge nodes."""

    def __init__(self):
        self._nodes: Dict[str, NodeRegistration] = {}
        self._last_heartbeat: Dict[str, float] = {}

    def register(self, node: NodeRegistration) -> None:
        self._nodes[node.node_id] = node
        self.record_heartbeat(node.node_id)

    def record_heartbeat(self, node_id: str) -> None:
        if node_id in self._nodes:
            self._last_heartbeat[node_id] = datetime.now(timezone.utc).timestamp()

    def get_node(self, node_id: str) -> Optional[NodeRegistration]:
        return self._nodes.get(node_id)

    def list_nodes(self) -> List[NodeRegistration]:
        return list(self._nodes.values())

    def is_online(self, node_id: str, timeout_seconds: int = 120) -> bool:
        last = self._last_heartbeat.get(node_id)
        if not last:
            return False
        return (datetime.now(timezone.utc).timestamp() - last) <= timeout_seconds

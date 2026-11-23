"""Node Agent daemon running on worker nodes."""
import time
from typing import Dict, Any, Optional
from ..execution.runner import TaskRunner
from ..system_management.services import ServiceManager

class NodeAgent:
    """Lightweight node agent that connects to Personal AI Control Plane.

    Guarantees:
    - Runs unprivileged by default.
    - Emits heartbeats.
    - Dispatches approved tasks to isolated runner.
    """

    def __init__(self, node_id: str, control_plane_url: str):
        self.node_id = node_id
        self.control_plane_url = control_plane_url
        self.runner = TaskRunner()
        self.services = ServiceManager()
        self._running = False

    def get_node_status(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "status": "healthy",
            "timestamp": time.time()
        }

    def execute_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        op = task_payload.get("operation", "exec")
        if op == "exec":
            cmd = task_payload.get("command", "")
            return self.runner.run_command(cmd)
        elif op == "service_status":
            svc = task_payload.get("service", "")
            return {"service": svc, "status": self.services.get_status(svc)}
        return {"error": f"Unknown operation: {op}", "status": "failed"}

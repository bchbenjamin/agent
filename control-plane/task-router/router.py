"""Task Router for dispatching workloads to capable nodes."""

from typing import Any, Dict

from ..api.schema import TaskRequest
from ..authorization.scopes import ScopeValidator
from ..node_registry.registry import NodeRegistry


class TaskRouter:
    """Routes execution tasks to target nodes while enforcing authorization."""

    def __init__(self, registry: NodeRegistry):
        self.registry = registry

    def route_task(self, task: TaskRequest, granted_scopes: set) -> Dict[str, Any]:
        # 1. Scope check
        if not ScopeValidator.has_scope(granted_scopes, task.required_scope):
            return {
                "status": "denied",
                "error": f"Missing required scope: {task.required_scope}",
            }

        # 2. Explicit approval check
        if (
            ScopeValidator.requires_explicit_approval(task.operation)
            and not task.approved
        ):
            return {
                "status": "approval_required",
                "message": f"Operation '{task.operation}' requires explicit approval.",
            }

        # 3. Node availability check
        node = self.registry.get_node(task.target_node)
        if not node:
            return {
                "status": "error",
                "error": f"Target node '{task.target_node}' not registered.",
            }

        if not self.registry.is_online(task.target_node):
            return {
                "status": "queued",
                "message": f"Target node '{task.target_node}' is offline. Task queued for reconnect.",
            }

        return {
            "status": "queued",
            "task_id": task.task_id,
            "target_node": task.target_node,
            "operation": task.operation,
            "message": "Task is queued for the node's outbound polling loop.",
        }

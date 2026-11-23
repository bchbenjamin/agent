"""Security boundary tests verifying scope isolation and elevation requirements."""
import unittest
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from control_plane.authorization.scopes import (
    ScopeValidator,
    SCOPE_CONTEXT_READ,
    SCOPE_SERVICES_MANAGE,
    SCOPE_TERMINAL_EXECUTE,
)
from control_plane.task_router.router import TaskRouter
from control_plane.node_registry.registry import NodeRegistry
from control_plane.api.schema import TaskRequest, NodeRegistration

class TestPermissionBoundaries(unittest.TestCase):

    def setUp(self):
        self.registry = NodeRegistry()
        self.registry.register(NodeRegistration(
            node_id="pi5",
            hostname="raspberrypi",
            architecture="aarch64",
            ram_mb=4096,
            tier="primary_worker",
            capabilities=["terminal", "beeper", "screen"]
        ))
        self.router = TaskRouter(self.registry)

    def test_scope_isolation_blocks_unauthorized_scope(self):
        # Client only has context:read
        client_scopes = {SCOPE_CONTEXT_READ}

        task = TaskRequest(
            task_id="t1",
            target_node="pi5",
            operation="terminal:run",
            payload={"cmd": "ls"},
            required_scope=SCOPE_TERMINAL_EXECUTE,
            client_id="morphic-user",
            user_identity="bchbenjamin"
        )

        res = self.router.route_task(task, client_scopes)
        self.assertEqual(res["status"], "denied")
        self.assertIn("Missing required scope", res["error"])

    def test_destructive_operation_blocked_without_approval(self):
        # Client has admin scope, but destructive action lacks explicit approval
        admin_scopes = {SCOPE_SERVICES_MANAGE}

        destructive_task = TaskRequest(
            task_id="t2",
            target_node="pi5",
            operation="services:stop",
            payload={"service": "beeper.service"},
            required_scope=SCOPE_SERVICES_MANAGE,
            client_id="admin-client",
            user_identity="bchbenjamin",
            requires_approval=True,
            approved=False  # NOT approved
        )

        res = self.router.route_task(destructive_task, admin_scopes)
        self.assertEqual(res["status"], "approval_required")

if __name__ == "__main__":
    unittest.main()

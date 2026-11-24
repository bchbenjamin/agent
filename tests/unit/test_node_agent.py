"""Unit tests for Node Agent task execution and command restrictions."""

import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from node_agent.core.agent import NodeAgent
from node_agent.execution.runner import TaskRunner


class TestNodeAgent(unittest.TestCase):
    def setUp(self):
        self.runner = TaskRunner()
        self.agent = NodeAgent("pi5", "http://127.0.0.1:8000")

    def test_safe_command_execution(self):
        res = self.runner.run_command("echo 'HELLO_NODE_AGENT'")
        self.assertEqual(res["returncode"], 0)
        self.assertIn("HELLO_NODE_AGENT", res["stdout"])

    def test_forbidden_destructive_command(self):
        res = self.runner.run_command("wipefs /dev/sda")
        self.assertEqual(res["returncode"], 1)
        self.assertIn("rejected", res["error"])

    def test_node_agent_status(self):
        status = self.agent.get_node_status()
        self.assertEqual(status["node_id"], "pi5")
        self.assertEqual(status["status"], "healthy")

    def test_outbound_poll_and_result_reporting(self):
        import httpx

        reported = {}

        def handler(request):
            self.assertEqual(request.headers["authorization"], "Bearer node-test-token")
            if request.url.path.endswith("/heartbeat"):
                return httpx.Response(200, json={"status": "ok"})
            if request.url.path.endswith("/tasks/next"):
                return httpx.Response(
                    200,
                    json={
                        "task": {
                            "task_id": "task-node-test",
                            "operation": "exec",
                            "payload": {"argv": ["/bin/echo", "node-task"]},
                            "approved": False,
                        }
                    },
                )
            if request.url.path.endswith("/result"):
                reported.update(
                    request.read() and __import__("json").loads(request.content)
                )
                return httpx.Response(200, json={"status": "recorded"})
            raise AssertionError(f"Unexpected request: {request.url}")

        client = httpx.Client(transport=httpx.MockTransport(handler), trust_env=False)
        agent = NodeAgent(
            "pi5", "http://pai.test", "node-test-token", http_client=client
        )
        self.assertTrue(agent.run_once())
        self.assertEqual(reported["result"]["stdout"].strip(), "node-task")
        self.assertEqual(reported["result"]["returncode"], 0)
        client.close()


if __name__ == "__main__":
    unittest.main()

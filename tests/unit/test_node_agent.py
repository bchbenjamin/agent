"""Unit tests for Node Agent task execution and command restrictions."""
import unittest
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from node_agent.execution.runner import TaskRunner
from node_agent.core.agent import NodeAgent

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

if __name__ == "__main__":
    unittest.main()

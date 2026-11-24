"""Integration tests verifying Layer 1 AI Gateway isolation."""
import unittest
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from personal_ai_api.integrations.gateway_client import AIGatewayClient
from integrations.ai_gateway.client import test_ai_gateway_health as check_ai_gateway_health

@unittest.skipUnless(os.getenv("PAI_RUN_EXTERNAL_INTEGRATION") == "1", "set PAI_RUN_EXTERNAL_INTEGRATION=1 to call live services")
class TestAIGatewayIsolation(unittest.TestCase):

    def test_gateway_health(self):
        # AI Gateway public health check with realistic network timeout
        healthy = check_ai_gateway_health(timeout=20)
        self.assertTrue(healthy, "AI Gateway health endpoint should respond with status ok.")

    def test_isolation_architecture_properties(self):
        client = AIGatewayClient()
        # Verify base URL points to external gateway
        self.assertIn("ai.bchbenjamin.in", client.base_url)
        # Client must not contain any inbound listeners or personal file references
        self.assertFalse(hasattr(client, "serve"))
        self.assertFalse(hasattr(client, "listen"))

if __name__ == "__main__":
    unittest.main()

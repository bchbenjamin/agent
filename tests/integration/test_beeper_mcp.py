"""Integration tests for Beeper Desktop local MCP endpoint."""
import unittest
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from integrations.beeper.client import check_beeper_api

@unittest.skipUnless(os.getenv("PAI_RUN_EXTERNAL_INTEGRATION") == "1", "set PAI_RUN_EXTERNAL_INTEGRATION=1 to call the Pi Beeper endpoint")
class TestBeeperMCP(unittest.TestCase):

    def test_beeper_local_api(self):
        # Beeper local API endpoint should be running and return HTTP 401 (OAuth expected)
        res = check_beeper_api()
        self.assertIn(res.get("status"), ["active_oauth", "ok"], f"Beeper API status unexpected: {res}")
        self.assertIn(res.get("code"), [200, 401])

if __name__ == "__main__":
    unittest.main()

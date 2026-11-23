"""Unit tests for token authentication and scope validation."""
import unittest
import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from control_plane.authentication.tokens import TokenManager
from control_plane.authorization.scopes import (
    ScopeValidator,
    SCOPE_CONTEXT_READ,
    SCOPE_NODES_READ,
    SCOPE_TERMINAL_EXECUTE,
    SCOPE_NODES_ADMIN,
)

class TestAuthScopes(unittest.TestCase):

    def setUp(self):
        self.tm = TokenManager()

    def test_token_issuance_and_verification(self):
        token = self.tm.issue_token(
            client_id="morphic-client",
            client_type="morphic",
            user="bchbenjamin",
            scopes={SCOPE_CONTEXT_READ, SCOPE_NODES_READ}
        )
        self.assertTrue(token.startswith("pai_morphic_"))

        meta = self.tm.verify_token(token)
        self.assertIsNotNone(meta)
        self.assertEqual(meta["client_id"], "morphic-client")
        self.assertIn(SCOPE_CONTEXT_READ, meta["scopes"])

    def test_revoked_token(self):
        token = self.tm.issue_token("test-client", "mcp", "bchbenjamin", {SCOPE_NODES_READ})
        self.tm.revoke_token(token)
        self.assertIsNone(self.tm.verify_token(token))

    def test_scope_validation(self):
        granted = {SCOPE_CONTEXT_READ, SCOPE_NODES_READ}
        self.assertTrue(ScopeValidator.has_scope(granted, SCOPE_CONTEXT_READ))
        self.assertFalse(ScopeValidator.has_scope(granted, SCOPE_TERMINAL_EXECUTE))

        # Admin scope supersedes
        admin_granted = {SCOPE_NODES_ADMIN}
        self.assertTrue(ScopeValidator.has_scope(admin_granted, SCOPE_TERMINAL_EXECUTE))

    def test_destructive_approval_detection(self):
        self.assertTrue(ScopeValidator.requires_explicit_approval("storage:format"))
        self.assertTrue(ScopeValidator.requires_explicit_approval("system:reboot"))
        self.assertFalse(ScopeValidator.requires_explicit_approval("nodes:list"))

if __name__ == "__main__":
    unittest.main()

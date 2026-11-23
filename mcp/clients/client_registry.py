"""MCP Client Registry tracking registered external AI clients."""
from typing import Dict, Any, List

class MCPClientRegistry:
    """Tracks authorized MCP clients and their granted scopes."""

    def __init__(self):
        self._clients: Dict[str, Dict[str, Any]] = {
            "claude-desktop": {
                "name": "Claude Desktop Client",
                "scopes": ["context:read", "nodes:read"],
                "revoked": False
            },
            "claude-code": {
                "name": "Claude Code CLI",
                "scopes": ["context:read", "nodes:read", "files:read", "terminal:execute"],
                "revoked": False
            }
        }

    def get_client(self, client_id: str) -> Dict[str, Any]:
        return self._clients.get(client_id, {})

    def is_authorized(self, client_id: str, scope: str) -> bool:
        client = self._clients.get(client_id)
        if not client or client.get("revoked"):
            return False
        return scope in client.get("scopes", [])

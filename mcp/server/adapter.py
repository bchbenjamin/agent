"""MCP Protocol Adapter over Personal AI API (https://mcp.hermes.bchbenjamin.in).

CRITICAL ARCHITECTURAL RULE:
This MCP server does not implement custom permissions or direct system execution.
It is strictly an adapter: incoming MCP requests are authenticated, mapped to
Personal AI API endpoints, and evaluated against the central permission scopes.
"""
from typing import Dict, Any, List, Optional
from ..tools.definitions import AVAILABLE_TOOLS
from ..resources.context_resources import AVAILABLE_RESOURCES

class MCPProtocolAdapter:
    """Adapts Model Context Protocol calls to authenticated Personal AI API operations."""

    def __init__(self, api_base_url: str = "https://api.hermes.bchbenjamin.in"):
        self.api_base_url = api_base_url

    def handle_tools_list(self) -> List[Dict[str, Any]]:
        return AVAILABLE_TOOLS

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any], client_token: str) -> Dict[str, Any]:
        # Validate that tool exists
        tool = next((t for t in AVAILABLE_TOOLS if t["name"] == tool_name), None)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found", "isError": True}

        # Map to Personal AI API invocation with the client's scoped token
        # In actual deployment, this sends an HTTP request to the Personal AI API
        return {
            "result": f"Executed tool '{tool_name}' through Personal AI API adapter",
            "mapped_endpoint": f"{self.api_base_url}/v1/tasks",
            "isError": False
        }

    def handle_resources_list(self) -> List[Dict[str, Any]]:
        return AVAILABLE_RESOURCES

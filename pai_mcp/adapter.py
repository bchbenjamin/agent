"""Thin MCP-to-Personal-AI API adapter; authorization remains in the API."""

from __future__ import annotations

from typing import Any

import httpx

AVAILABLE_TOOLS = [
    {
        "name": "list_nodes",
        "description": "List registered managed nodes and status.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_node_status",
        "description": "Get a managed node's status.",
        "inputSchema": {
            "type": "object",
            "properties": {"node_id": {"type": "string"}},
            "required": ["node_id"],
        },
    },
    {
        "name": "submit_task",
        "description": "Submit an authenticated node task; destructive tasks require approval.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"},
                "operation": {"type": "string"},
                "payload": {"type": "object"},
            },
            "required": ["node_id", "operation", "payload"],
        },
    },
    {
        "name": "get_task",
        "description": "Get task status and result.",
        "inputSchema": {
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
        },
    },
    {
        "name": "query_context",
        "description": "Search explicitly indexed personal context.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        },
    },
]


class MCPProtocolAdapter:
    def __init__(
        self,
        api_base_url: str = "https://api.hermes.bchbenjamin.in",
        client_token: str = "",
        http_client: httpx.Client | None = None,
    ):
        self.api_base_url = api_base_url.rstrip("/")
        self.client_token = client_token
        self.http = http_client or httpx.Client(timeout=30, trust_env=False)

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        client_token: str | None = None,
    ) -> dict[str, Any]:
        token = client_token or self.client_token
        if not token:
            raise RuntimeError("A client-scoped Personal AI API token is required")
        response = self.http.request(
            method,
            self.api_base_url + path,
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        response.raise_for_status()
        return response.json() if response.content else {"status": "ok"}

    def handle_tools_list(self):
        return AVAILABLE_TOOLS

    def handle_tool_call(
        self, tool_name: str, arguments: dict[str, Any], client_token: str | None = None
    ):
        routes = {
            "list_nodes": ("GET", "/v1/nodes", None),
            "get_node_status": (
                "GET",
                f"/v1/nodes/{arguments.get('node_id', '')}",
                None,
            ),
            "submit_task": (
                "POST",
                "/v1/tasks",
                {
                    "target_node": arguments.get("node_id"),
                    "operation": arguments.get("operation"),
                    "payload": arguments.get("payload", {}),
                },
            ),
            "get_task": ("GET", f"/v1/tasks/{arguments.get('task_id', '')}", None),
            "query_context": (
                "POST",
                "/v1/context/query",
                {
                    "query": arguments.get("query", ""),
                    "limit": arguments.get("limit", 10),
                },
            ),
        }
        if tool_name not in routes:
            return {"error": f"Unknown tool: {tool_name}", "isError": True}
        method, path, payload = routes[tool_name]
        try:
            return {
                "result": self._request(method, path, payload, client_token),
                "isError": False,
            }
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"Personal AI API returned HTTP {exc.response.status_code}",
                "status_code": exc.response.status_code,
                "isError": True,
            }

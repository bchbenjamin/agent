"""MCP adapter delegates every operation to the authenticated API."""

import httpx

from pai_mcp.adapter import AVAILABLE_TOOLS, MCPProtocolAdapter


def test_adapter_forwards_scoped_bearer_and_maps_tool_calls():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"nodes": [{"node_id": "pi5"}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = MCPProtocolAdapter("http://pai.test", "client-token", client)
    result = adapter.handle_tool_call("list_nodes", {})
    assert result["isError"] is False
    assert result["result"]["nodes"][0]["node_id"] == "pi5"
    assert seen[0].url.path == "/v1/nodes"
    assert seen[0].headers["authorization"] == "Bearer client-token"
    assert len(AVAILABLE_TOOLS) == 5


def test_unknown_mcp_tool_is_rejected_without_api_call():
    adapter = MCPProtocolAdapter(
        "http://pai.test",
        "client-token",
        httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(200, json={}))
        ),
    )
    assert adapter.handle_tool_call("run_root", {})["isError"] is True


def test_official_mcp_server_registers_expected_tools():
    from pai_mcp.server import server

    names = {tool.name for tool in server._tool_manager.list_tools()}
    assert names == {
        "list_nodes",
        "get_node_status",
        "submit_task",
        "get_task",
        "query_context",
    }

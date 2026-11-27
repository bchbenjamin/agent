import asyncio

import pytest

import pai_mcp.server as mcp_server


def test_native_history_tools_require_separate_scope(monkeypatch):
    monkeypatch.setattr(mcp_server, "client_capabilities", lambda: {"scopes": {"context:read"}})
    with pytest.raises(PermissionError, match="history scope"):
        mcp_server.list_native_conversations()
    with pytest.raises(PermissionError, match="history scope"):
        mcp_server.read_native_conversation("telegram-session")


def test_box_probe_tool_requires_execution_scope(monkeypatch):
    monkeypatch.setattr(mcp_server, "client_capabilities", lambda: {"scopes": {"box:read"}})
    with pytest.raises(PermissionError, match="execution scope"):
        asyncio.run(mcp_server.box_health_probe("hostname"))


def test_scoped_tools_delegate_after_authorization(monkeypatch):
    monkeypatch.setattr(
        mcp_server,
        "client_capabilities",
        lambda: {"scopes": {"sessions:read", "box:execute"}},
    )
    monkeypatch.setattr(mcp_server, "_list_native_conversations", lambda offset, limit: {"sessions": []})
    monkeypatch.setattr(mcp_server, "_read_native_conversation", lambda session_id, offset, limit: {"session_id": session_id})
    async def probe(command, scopes):
        return {"command": command}

    monkeypatch.setattr(mcp_server, "call_box_probe", probe)
    assert mcp_server.list_native_conversations() == {"sessions": []}
    assert mcp_server.read_native_conversation("telegram-session")["session_id"] == "telegram-session"
    assert asyncio.run(mcp_server.box_health_probe("hostname")) == {"command": "hostname"}

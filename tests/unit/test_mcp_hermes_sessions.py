import pytest

from pai_mcp import hermes_sessions


class FakeResponse:
    is_success = True

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self, response_sink, **kwargs):
        self.response_sink = response_sink

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url, params, headers):
        assert headers["Authorization"] == "Bearer test-key"
        self.response_sink.append((url, params))
        return FakeResponse(self.response_sink.payload)


class FakeCalls(list):
    payload = None


def test_list_native_conversations_is_paginated_and_metadata_only(monkeypatch):
    calls = FakeCalls()
    calls.payload = {
        "data": [{"id": "telegram-1", "title": "private title", "source": "telegram", "preview": "private body"}],
        "offset": 10,
        "limit": 20,
        "has_more": True,
    }
    monkeypatch.setenv("PAI_HERMES_API_KEY", "test-key")
    monkeypatch.setattr(hermes_sessions.httpx, "Client", lambda **kw: FakeClient(calls, **kw))
    result = hermes_sessions.list_native_conversations(10, 20)
    assert result["sessions"] == [{"id": "telegram-1", "title": "private title", "source": "telegram"}]
    assert result["pagination"]["has_more"] is True
    assert calls[0][1] == {"offset": 10, "limit": 20}


def test_read_native_conversation_preserves_tool_data_but_strips_reasoning(monkeypatch):
    calls = FakeCalls()
    calls.payload = {
        "session_id": "telegram-1",
        "data": [{"role": "tool", "content": "hostname output", "tool_name": "terminal", "tool_call_id": "tc1", "tool_calls": [], "reasoning": "private internal reasoning"}],
        "pagination": {"offset": 0, "limit": 20, "returned": 1},
    }
    monkeypatch.setenv("PAI_HERMES_API_KEY", "test-key")
    monkeypatch.setattr(hermes_sessions.httpx, "Client", lambda **kw: FakeClient(calls, **kw))
    result = hermes_sessions.read_native_conversation("telegram-1", 0, 20)
    assert result["messages"][0]["content"] == "hostname output"
    assert result["messages"][0]["tool_call_id"] == "tc1"
    assert "reasoning" not in result["messages"][0]


def test_history_requires_key_and_loopback_url(monkeypatch):
    monkeypatch.delenv("PAI_HERMES_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="not configured"):
        hermes_sessions.list_native_conversations()
    monkeypatch.setenv("PAI_HERMES_API_KEY", "test-key")
    monkeypatch.setenv("PAI_HERMES_API_BASE_URL", "https://example.org")
    with pytest.raises(ValueError, match="loopback"):
        hermes_sessions.list_native_conversations()
    monkeypatch.setenv("PAI_HERMES_API_BASE_URL", "http://127.0.0.1:9999")
    with pytest.raises(ValueError, match="loopback"):
        hermes_sessions.list_native_conversations()
    monkeypatch.setenv("PAI_HERMES_API_BASE_URL", "http://127.0.0.1:8642")
    with pytest.raises(ValueError, match="pagination"):
        hermes_sessions.list_native_conversations(limit=1000)
    with pytest.raises(ValueError, match="identifier"):
        hermes_sessions.read_native_conversation("..")


def test_box_probe_is_fixed_and_scope_gated():
    import asyncio
    from pai_mcp.integrations import call_box_probe

    with pytest.raises(PermissionError, match="scope"):
        asyncio.run(call_box_probe("hostname", {"box:read"}))
    with pytest.raises(PermissionError, match="fixed"):
        asyncio.run(call_box_probe("rm -rf /", {"box:execute"}))

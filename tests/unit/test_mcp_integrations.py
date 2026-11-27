import asyncio
import pytest
from pai_mcp.integrations import available_integrations, call_readonly

def test_federation_scopes_and_opt_in(monkeypatch):
    monkeypatch.setenv("PAI_BOX_MCP_TOKEN", "synthetic-test-token")
    assert available_integrations(set()) == {"integrations": []}
    record = available_integrations({"box:read"})["integrations"][0]
    assert record == {"name": "box", "configured": True, "allowed_tools": ["box_list"]}
    with pytest.raises(PermissionError):
        asyncio.run(call_readonly("box", "box_list", {}, {"beeper:read"}))
    with pytest.raises(PermissionError):
        asyncio.run(call_readonly("box", "shell", {}, {"box:read"}))
    with pytest.raises(PermissionError):
        asyncio.run(call_readonly("beeper", "send_message", {}, {"beeper:read"}))
    with pytest.raises(ValueError):
        asyncio.run(call_readonly("http://untrusted.example", "box_list", {}, {"box:read"}))

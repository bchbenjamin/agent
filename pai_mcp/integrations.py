"""Read-only, opt-in federation of existing MCP services, without model inference."""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Never accept caller-supplied URLs, headers, commands, or upstream tool aliases.
SERVICES = {
    "box": ("https://mcp.box.simular.ai/mcp", "PAI_BOX_MCP_TOKEN", "box:read", frozenset({"box_list"})),
    "beeper": ("http://127.0.0.1:23373/v0/mcp", "PAI_BEEPER_MCP_TOKEN", "beeper:read", frozenset({"get_accounts", "get_chat", "search_chats", "search_messages", "list_messages"})),
}


def available_integrations(scopes: set[str]) -> dict[str, Any]:
    return {"integrations": [
        {"name": name, "configured": bool(os.environ.get(token_env)), "allowed_tools": sorted(tools)}
        for name, (_, token_env, scope, tools) in SERVICES.items()
        if scope in scopes or "nodes:admin" in scopes
    ]}


async def call_readonly(name: str, tool: str, arguments: dict[str, Any], scopes: set[str]) -> dict[str, Any]:
    if name not in SERVICES:
        raise ValueError("Unknown integration")
    url, token_env, scope, tools = SERVICES[name]
    if scope not in scopes and "nodes:admin" not in scopes:
        raise PermissionError("Integration scope required")
    if tool not in tools:
        raise PermissionError("Tool is not on the read-only allowlist")
    token = os.environ.get(token_env)
    if not token:
        raise RuntimeError("Integration not configured")
    if len(json.dumps(arguments, ensure_ascii=False).encode()) > 8192:
        raise ValueError("Integration arguments exceed 8 KiB")
    try:
        async with asyncio.timeout(35):
            async with streamablehttp_client(url, headers={"Authorization": f"Bearer {token}"}, timeout=15, sse_read_timeout=30) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    discovery = await session.list_tools()
                    if tool not in {t.name for t in discovery.tools}:
                        raise ValueError("Tool unavailable on installed upstream")
                    result = await session.call_tool(tool, arguments)
        payload = result.model_dump(mode="json", exclude_none=True)
        # Only bounded text/structured content; no session IDs, resource handles, or
        # screenshots. Private view URLs are not needed for external box inventory.
        def clean(value):
            if isinstance(value, dict):
                return {k: clean(v) for k, v in value.items() if k not in {"view_url", "mcp_url", "_meta"}}
            if isinstance(value, list):
                return [clean(v) for v in value]
            return value
        structured = payload.get("structuredContent")
        if structured is not None:
            output = clean(structured)
        elif name == "box":
            # Box text may embed private view URLs. Parse JSON or return a clear error.
            output = []
            for item in payload.get("content", []):
                if item.get("type") == "text":
                    output.append(clean(json.loads(item["text"])))
        else:
            output = [item["text"] for item in payload.get("content", []) if item.get("type") == "text"]
        if len(json.dumps(output, ensure_ascii=False).encode()) > 96000:
            raise ValueError("Result too large; narrow the query")
        return {"integration": name, "tool": tool, "is_error": bool(payload.get("isError")), "result": output}
    except (PermissionError, ValueError):
        raise
    except Exception as exc:
        # Do not leak endpoint credentials, raw headers, or remote exception text.
        raise RuntimeError(f"Upstream integration failed ({type(exc).__name__})") from None

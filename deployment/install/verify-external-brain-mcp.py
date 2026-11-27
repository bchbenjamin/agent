"""Read-only local production MCP discovery and restricted-client identity check."""
from __future__ import annotations

import asyncio
import stat
import sys
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

EXPECTED = {
    "list_nodes", "get_node_status", "submit_task", "get_task", "query_context",
    "client_capabilities", "read_context_document", "remember_context",
    "list_integrations", "read_integration", "box_health_probe",
    "list_native_conversations", "read_native_conversation",
}


async def verify(token: str, url: str = "http://127.0.0.1:8765/mcp") -> None:
    async with asyncio.timeout(12):
        async with streamablehttp_client(
            url, headers={"Authorization": f"Bearer {token}"}, timeout=5,
            sse_read_timeout=5,
            httpx_client_factory=lambda **kw: httpx.AsyncClient(**kw, trust_env=False),
        ) as (read, send, _):
            async with ClientSession(read, send) as session:
                await session.initialize()
                names = {t.name for t in (await session.list_tools()).tools}
                missing = EXPECTED - names
                if missing:
                    raise ValueError(f"Missing expected MCP tools: {', '.join(sorted(missing))}")
                identity = await session.call_tool("client_capabilities", {})
                if identity.isError or not isinstance(identity.structuredContent, dict):
                    raise RuntimeError("Restricted client identity check failed")
                details = identity.structuredContent
                scopes = set(details.get("scopes", []))
                if details.get("client_type") != "external-brain" or scopes & {"tasks:approve", "nodes:admin"}:
                    raise RuntimeError("Unexpected credential type or privileged scopes")
                print(f"Verified {len(names)} live MCP tools and restricted external-brain identity.")


async def wait_for_mcp(token: str) -> None:
    for attempt in range(3):
        try:
            await verify(token)
            return
        except Exception as exc:
            if attempt == 2:
                # Do not print upstream errors, headers, or tokens.
                raise SystemExit(f"MCP verification failed ({type(exc).__name__}). Credential retained; inspect service status and rerun the verifier.") from None
            await asyncio.sleep(2)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify-external-brain-mcp.py TOKEN_FILE")
    path = Path(sys.argv[1])
    if path.is_symlink() or not path.is_file() or stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise SystemExit("Expected a regular token file with mode 0600")
    token = path.read_text().strip()
    if not token.startswith("pai_external-brain_"):
        raise SystemExit("Unexpected token format")
    asyncio.run(wait_for_mcp(token))

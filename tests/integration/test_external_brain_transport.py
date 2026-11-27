"""Real MCP Streamable HTTP round trip, with temporary DB and isolated services."""
import asyncio
import importlib.util
from pathlib import Path
import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager

import httpx
import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from control_plane.storage import SQLiteStore


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def service(args, env, port):
    process = subprocess.Popen([sys.executable, *args], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            if process.poll() is not None:
                pytest.fail("Isolated service exited before readiness")
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    break
            except OSError:
                time.sleep(0.05)
        else:
            pytest.fail("Isolated service did not start")
        yield
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def test_external_brain_real_transport(tmp_path):
    api_port, mcp_port = free_port(), free_port()
    while mcp_port == api_port:
        mcp_port = free_port()
    db = tmp_path / "transport.sqlite3"
    store = SQLiteStore(str(db))
    writer = store.issue_token("external-test", "external-brain", "owner", {"context:read", "context:write", "nodes:read", "terminal:execute"})
    reader = store.issue_token("hermes-test", "mcp", "owner", {"context:read"})
    env = dict(os.environ, PAI_DB_PATH=str(db), PAI_BOOTSTRAP_TOKEN="", PAI_API_TOKEN="",
               PAI_API_URL=f"http://127.0.0.1:{api_port}", PAI_MCP_HOST="127.0.0.1",
               PAI_MCP_PORT=str(mcp_port), PAI_MCP_TRANSPORT="streamable-http",
               PAI_HTTP_TRUST_ENV="false", NO_PROXY="127.0.0.1,localhost",
               PAI_BOX_MCP_TOKEN="", PAI_BEEPER_MCP_TOKEN="")
    url = f"http://127.0.0.1:{mcp_port}/mcp"

    async def session_roundtrip(token, write=False, document_id=None):
        async with streamablehttp_client(url, headers={"Authorization": f"Bearer {token}"}, timeout=5, sse_read_timeout=5, httpx_client_factory=lambda **kw: httpx.AsyncClient(**kw, trust_env=False)) as (read, send, _):
            async with ClientSession(read, send) as session:
                init = await session.initialize()
                assert "query_context" in init.instructions
                names = {t.name for t in (await session.list_tools()).tools}
                assert {"client_capabilities", "remember_context", "read_context_document", "read_integration"} <= names
                identity = await session.call_tool("client_capabilities", {})
                assert not identity.isError
                if write:
                    result = await session.call_tool("remember_context", {"title": "transport proof", "body": "Synthetic external-brain transport test.", "owner_confirmed": True})
                    assert not result.isError, result.content
                    assert result.structuredContent["status"] == "indexed"
                    return result.structuredContent["document_id"]
                result = await session.call_tool("read_context_document", {"document_id": document_id})
                assert not result.isError, result.content
                assert result.structuredContent["body"] == "Synthetic external-brain transport test."
                denied = await session.call_tool("remember_context", {"title": "denied", "body": "synthetic", "owner_confirmed": True})
                assert denied.isError

    with service(["-m", "uvicorn", "personal_ai_api.server.app:app", "--host", "127.0.0.1", "--port", str(api_port)], env, api_port):
        with service(["-m", "pai_mcp.server"], env, mcp_port):
            assert httpx.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, timeout=5, trust_env=False).status_code == 401
            document_id = asyncio.run(session_roundtrip(writer, write=True))
            path = Path(__file__).resolve().parents[2] / "deployment/install/verify-external-brain-mcp.py"
            spec = importlib.util.spec_from_file_location("verify_external_brain", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            asyncio.run(module.verify(writer, url))

        # New MCP process, same private data store.
        with service(["-m", "pai_mcp.server"], env, mcp_port):
            asyncio.run(session_roundtrip(reader, document_id=document_id))

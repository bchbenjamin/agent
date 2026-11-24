"""Official MCP SDK server; all authority is enforced by Personal AI API."""

from __future__ import annotations

import contextvars
import os
from typing import Any

import httpx
import uvicorn
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware

api_token_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "pai_mcp_token", default=None
)
API_URL = os.environ.get("PAI_API_URL", "https://api.hermes.bchbenjamin.in").rstrip("/")
HTTP_TRUST_ENV = os.environ.get("PAI_HTTP_TRUST_ENV", "false").lower() == "true"
server = FastMCP(
    "Personal AI Infrastructure",
    instructions="Use the authenticated Personal AI API for node status, task execution, and indexed personal context.",
    host=os.environ.get("PAI_MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("PAI_MCP_PORT", "8765")),
    streamable_http_path="/mcp",
    stateless_http=True,
)


def _token() -> str:
    token = api_token_var.get() or os.environ.get("PAI_API_TOKEN")
    if not token:
        raise RuntimeError("No Personal AI API bearer token is available")
    return token


def _api(
    method: str, path: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {_token()}", "Accept": "application/json"}
    with httpx.Client(timeout=30, trust_env=HTTP_TRUST_ENV) as client:
        response = client.request(
            method, f"{API_URL}{path}", headers=headers, json=payload
        )
        response.raise_for_status()
        if not response.content:
            return {"status": "ok"}
        return response.json()


@server.tool()
def list_nodes() -> dict[str, Any]:
    """List registered managed nodes and their live/offline status."""
    return _api("GET", "/v1/nodes")


@server.tool()
def get_node_status(node_id: str) -> dict[str, Any]:
    """Get detailed status for one managed node."""
    return _api("GET", f"/v1/nodes/{node_id}")


@server.tool()
def submit_task(
    node_id: str, operation: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Submit a node task. Destructive operations return approval_required until approved."""
    return _api(
        "POST",
        "/v1/tasks",
        {
            "target_node": node_id,
            "operation": operation,
            "payload": payload,
        },
    )


@server.tool()
def get_task(task_id: str) -> dict[str, Any]:
    """Retrieve task status and execution result."""
    return _api("GET", f"/v1/tasks/{task_id}")


@server.tool()
def query_context(query: str, limit: int = 10) -> dict[str, Any]:
    """Search explicitly indexed personal context and infrastructure documentation."""
    return _api("POST", "/v1/context/query", {"query": query, "limit": limit})


class PersonalAIBearerMiddleware(BaseHTTPMiddleware):
    """Authenticate incoming Streamable HTTP MCP clients with API-issued tokens."""

    async def dispatch(self, request, call_next):
        authorization = request.headers.get("authorization", "")
        if not authorization.startswith("Bearer "):
            return JSONResponse({"error": "Bearer token required"}, status_code=401)
        token = authorization[7:].strip()
        try:
            async with httpx.AsyncClient(timeout=8, trust_env=HTTP_TRUST_ENV) as client:
                response = await client.get(
                    f"{API_URL}/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                )
            if response.status_code != 200:
                return JSONResponse(
                    {"error": "Invalid Personal AI API credential"}, status_code=401
                )
        except httpx.HTTPError:
            return JSONResponse(
                {"error": "Personal AI API authentication service unavailable"},
                status_code=503,
            )
        reset = api_token_var.set(token)
        try:
            return await call_next(request)
        finally:
            api_token_var.reset(reset)


def main() -> None:
    transport = os.environ.get("PAI_MCP_TRANSPORT", "stdio")
    if transport == "stdio":
        token = os.environ.get("PAI_API_TOKEN")
        if not token:
            raise SystemExit("PAI_API_TOKEN is required for stdio transport")
        reset = api_token_var.set(token)
        try:
            server.run(transport="stdio")
        finally:
            api_token_var.reset(reset)
    elif transport == "streamable-http":
        app = server.streamable_http_app()
        app.add_middleware(PersonalAIBearerMiddleware)
        uvicorn.run(
            app,
            host=os.environ.get("PAI_MCP_HOST", "127.0.0.1"),
            port=int(os.environ.get("PAI_MCP_PORT", "8765")),
            log_level=os.environ.get("PAI_LOG_LEVEL", "info"),
        )
    else:
        raise SystemExit("PAI_MCP_TRANSPORT must be 'stdio' or 'streamable-http'")


if __name__ == "__main__":
    main()

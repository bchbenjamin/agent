"""Read-only, scope-gated access to the installed Hermes session API."""
from __future__ import annotations

import json
import os
import re
from urllib.parse import urlsplit

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8642"
SESSION_FIELDS = (
    "id", "title", "source", "started_at", "last_active", "ended_at",
    "message_count", "tool_call_count", "pinned", "archived",
)
MESSAGE_FIELDS = (
    "id", "role", "content", "timestamp", "display_kind", "tool_name",
    "tool_call_id", "tool_calls", "finish_reason",
)


def _base_url() -> str:
    value = os.environ.get("PAI_HERMES_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.port not in {None, 8642}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Hermes history API must use loopback HTTP")
    return value


def _request(path: str, params: dict[str, int]) -> dict:
    key = os.environ.get("PAI_HERMES_API_KEY", "")
    if not key:
        raise RuntimeError("Hermes history integration is not configured")
    try:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.get(
                _base_url() + path,
                params=params,
                headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
            )
        if not response.is_success:
            raise RuntimeError(f"Hermes history API returned HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Hermes history API returned an invalid response")
        return payload
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Hermes history API unavailable ({type(exc).__name__})") from None


def list_native_conversations(offset: int = 0, limit: int = 20) -> dict:
    if not 0 <= offset <= 1_000_000 or not 1 <= limit <= 50:
        raise ValueError("Invalid conversation pagination")
    payload = _request("/api/sessions", {"offset": offset, "limit": limit})
    rows = payload.get("data", [])
    if not isinstance(rows, list):
        raise RuntimeError("Hermes history API returned invalid session data")
    sessions = [
        {key: row[key] for key in SESSION_FIELDS if key in row}
        for row in rows if isinstance(row, dict)
    ]
    return {
        "sessions": sessions,
        "pagination": {
            "offset": payload.get("offset", offset),
            "limit": payload.get("limit", limit),
            "has_more": bool(payload.get("has_more", False)),
        },
    }


def read_native_conversation(session_id: str, offset: int = 0, limit: int = 20) -> dict:
    if (
        not session_id
        or session_id in {".", ".."}
        or len(session_id) > 160
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*", session_id)
    ):
        raise ValueError("Invalid session identifier")
    if not 0 <= offset <= 1_000_000 or not 1 <= limit <= 50:
        raise ValueError("Invalid message pagination")
    payload = _request(
        f"/api/sessions/{session_id}/messages", {"offset": offset, "limit": limit}
    )
    rows = payload.get("data", [])
    if not isinstance(rows, list):
        raise RuntimeError("Hermes history API returned invalid message data")
    messages = [
        {key: row[key] for key in MESSAGE_FIELDS if key in row}
        for row in rows if isinstance(row, dict)
    ]
    # Reasoning fields and other implementation metadata are intentionally omitted.
    result = {
        "session_id": payload.get("session_id", session_id),
        "messages": messages,
        "pagination": payload.get("pagination", {"offset": offset, "limit": limit}),
    }
    if len(json.dumps(result, ensure_ascii=False).encode("utf-8")) > 96_000:
        raise ValueError("Conversation page is too large; request a smaller page")
    return result

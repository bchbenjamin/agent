"""Hermes service client."""
import json
import urllib.request
from typing import Dict, Any

def test_hermes_connection(host: str = "127.0.0.1", port: int = 8642) -> bool:
    try:
        url = f"http://{host}:{port}/health"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return data.get("status") == "ok"
    except Exception:
        return False

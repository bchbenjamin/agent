"""Beeper Desktop local API health client."""
import urllib.request
from typing import Dict, Any

def check_beeper_api(host: str = "127.0.0.1", port: int = 23373) -> Dict[str, Any]:
    url = f"http://{host}:{port}/v0/mcp"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as resp:
            return {"status": "ok", "code": resp.status}
    except urllib.error.HTTPError as e:
        # HTTP 401 is expected for unauthenticated GET to OAuth MCP endpoint
        return {"status": "active_oauth", "code": e.code}
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}

"""Test client for Layer 1 AI Gateway verification."""
import json
import urllib.request
from typing import Dict, Any, Optional

def test_ai_gateway_health(base_url: str = "https://ai.bchbenjamin.in", timeout: int = 15) -> bool:
    try:
        url = f"{base_url.rstrip('/')}/health"
        req = urllib.request.Request(url, headers={"User-Agent": "PersonalAIInfrastructure/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            return data.get("status") == "ok"
    except Exception:
        return False

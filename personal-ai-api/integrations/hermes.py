"""Hermes Agent API client."""
import json
import urllib.request
from typing import Dict, Any, Optional

class HermesClient:
    """Client for communicating with Hermes API server (127.0.0.1:8642)."""

    def __init__(self, base_url: str = "http://127.0.0.1:8642", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def check_health(self) -> Dict[str, Any]:
        req = urllib.request.Request(f"{self.base_url}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())

    def list_models(self) -> Dict[str, Any]:
        req = urllib.request.Request(f"{self.base_url}/v1/models")
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())

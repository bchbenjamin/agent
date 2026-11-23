"""AI Gateway outbound client (Layer 1 Inference Client)."""
import json
import urllib.request
from typing import Dict, Any, List, Optional

class AIGatewayClient:
    """Outbound-only client for Layer 1 AI Gateway (https://ai.bchbenjamin.in).

    ARCHITECTURAL GUARANTEE:
    This client is strictly outbound. It communicates with the independent AI Gateway
    solely to request model completions. The AI Gateway has no network ingress into this
    service or node infrastructure.
    """

    def __init__(self, base_url: str = "https://ai.bchbenjamin.in/codex/v1", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def complete_chat(self, messages: List[Dict[str, str]], model: str = "ai-gateway") -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")

        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())

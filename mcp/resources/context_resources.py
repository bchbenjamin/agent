"""MCP Resources exposed by the Personal AI infrastructure."""
from typing import List, Dict, Any

AVAILABLE_RESOURCES: List[Dict[str, Any]] = [
    {
        "uri": "personal-ai://nodes/topology",
        "name": "Fleet Topology",
        "description": "Current infrastructure node specifications and network status",
        "mimeType": "application/json"
    },
    {
        "uri": "personal-ai://runbooks/pi5",
        "name": "Raspberry Pi 5 Runbook",
        "description": "Operating instructions and health verification steps for Pi 5",
        "mimeType": "text/markdown"
    }
]

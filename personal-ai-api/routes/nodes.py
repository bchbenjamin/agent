"""Nodes management routes."""
from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from ..auth.middleware import require_scope

router = APIRouter()

@router.get("/nodes")
def list_nodes(client: dict = Depends(require_scope("nodes:read"))) -> Dict[str, Any]:
    return {
        "nodes": [
            {
                "node_id": "pi5",
                "tier": "primary_worker",
                "status": "online",
                "tailscale_ip": "100.73.46.31"
            },
            {
                "node_id": "box",
                "tier": "auxiliary_compute_sandbox",
                "status": "configured"
            },
            {
                "node_id": "redmi",
                "tier": "edge_mobile_worker",
                "status": "staged"
            }
        ]
    }

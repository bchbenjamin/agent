"""Task dispatch routes."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from ..auth.middleware import require_scope

router = APIRouter()

@router.post("/tasks")
def submit_task(
    payload: Dict[str, Any],
    client: dict = Depends(require_scope("terminal:execute"))
) -> Dict[str, Any]:
    task_id = payload.get("task_id", "task_auto")
    target_node = payload.get("target_node", "pi5")
    operation = payload.get("operation", "exec")
    return {
        "status": "accepted",
        "task_id": task_id,
        "target_node": target_node,
        "operation": operation
    }

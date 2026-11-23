"""Personal context and indexed memory routes."""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from ..auth.middleware import require_scope

router = APIRouter()

@router.get("/context")
def get_context(
    query: str = "",
    client: dict = Depends(require_scope("context:read"))
) -> Dict[str, Any]:
    return {
        "status": "ok",
        "query": query,
        "results": []
    }

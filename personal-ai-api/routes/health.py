"""Health check route."""
from fastapi import APIRouter
from typing import Dict

router = APIRouter()

@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "personal-ai-api", "version": "1.0.0"}

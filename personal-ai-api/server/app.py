"""Personal AI API Server Application (https://api.hermes.bchbenjamin.in)."""
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List

from ..routes.health import router as health_router
from ..routes.nodes import router as nodes_router
from ..routes.tasks import router as tasks_router
from ..routes.context import router as context_router

app = FastAPI(
    title="Personal AI API",
    description="Central orchestration, personal context, and node management API.",
    version="1.0.0"
)

# Mount routes
app.include_router(health_router, tags=["Health"])
app.include_router(nodes_router, prefix="/v1", tags=["Nodes"])
app.include_router(tasks_router, prefix="/v1", tags=["Tasks"])
app.include_router(context_router, prefix="/v1", tags=["Context"])

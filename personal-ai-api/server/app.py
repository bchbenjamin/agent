"""Personal AI API application."""

import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from control_plane.authorization.scopes import ADMIN_SCOPES
from control_plane.storage import get_store, utcnow

from ..routes.auth import router as auth_router
from ..routes.context import router as context_router
from ..routes.health import router as health_router
from ..routes.nodes import router as nodes_router
from ..routes.tasks import router as tasks_router


def _bootstrap_admin() -> None:
    token = os.environ.get("PAI_BOOTSTRAP_TOKEN")
    if not token:
        return
    store = get_store()
    with store.connect() as db:
        db.execute(
            "INSERT INTO clients(client_id,client_type,user_identity,created_at,revoked) VALUES('bootstrap-admin','admin','owner',?,0) "
            "ON CONFLICT(client_id) DO UPDATE SET revoked=0",
            (utcnow(),),
        )
        db.execute(
            "INSERT INTO tokens(token_hash,client_id,scopes_json,created_at) VALUES(?,?,?,?) "
            "ON CONFLICT(token_hash) DO UPDATE SET revoked=0",
            (
                store.token_hash(token),
                "bootstrap-admin",
                json.dumps(sorted(ADMIN_SCOPES)),
                utcnow(),
            ),
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _bootstrap_admin()
    yield


app = FastAPI(
    title="Personal AI API",
    description="Authenticated personal context, node orchestration and task control plane.",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(health_router, tags=["Health"])
app.include_router(auth_router, prefix="/v1", tags=["Authentication"])
app.include_router(nodes_router, prefix="/v1", tags=["Nodes"])
app.include_router(tasks_router, prefix="/v1", tags=["Tasks"])
app.include_router(context_router, prefix="/v1", tags=["Context"])


@app.get("/")
def root():
    return {"service": "personal-ai-api", "docs": "/docs", "health": "/health"}

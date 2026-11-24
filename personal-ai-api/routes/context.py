"""Explicit personal-context indexing and scoped search endpoints."""

import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, model_validator

from control_plane.audit.logger import AuditLogger
from control_plane.storage import get_store

from ..auth.middleware import require_scope

router = APIRouter()


class ContextQuery(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=50)


class ContextIndexBody(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    source: str = Field(default="manual", max_length=1024)

    @model_validator(mode="after")
    def limit_document(self):
        if len(self.body.encode("utf-8")) > 1_000_000:
            raise ValueError("context document exceeds 1 MiB")
        if len(json.dumps({"title": self.title, "source": self.source})) > 4096:
            raise ValueError("context metadata exceeds 4 KiB")
        return self


@router.post("/context/index")
def index_context(
    body: ContextIndexBody, client: dict = Depends(require_scope("context:write"))
):
    document_id = get_store().add_document(body.title, body.body, body.source)
    AuditLogger().log(
        client["client_id"],
        client["user"],
        "personal-context",
        "context:index",
        body.source,
        "not_required",
        "success",
        None,
        {"document_id": document_id, "body_bytes": len(body.body.encode("utf-8"))},
    )
    return {"document_id": document_id, "status": "indexed"}


@router.post("/context/query")
def query_context(
    body: ContextQuery, client: dict = Depends(require_scope("context:read"))
):
    results = get_store().query_context(body.query, body.limit)
    return {"query": body.query, "results": results}

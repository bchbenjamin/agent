"""Explicit personal-context indexing and scoped search endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException, Path, Query
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
    if client["client_type"] == "external-brain":
        raise HTTPException(403, "External brains must use the provenance-scoped remember endpoint")
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


class ExternalMemoryBody(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=24000)
    kind: str = Field(pattern=r"^(memory|conversation)$", default="memory")
    owner_confirmed: bool = False

    @model_validator(mode="after")
    def validate_memory(self):
        if not self.owner_confirmed:
            raise ValueError("Explicit owner confirmation is required")
        if len(self.body.encode("utf-8")) > 96000:
            raise ValueError("Record exceeds 96 KiB")
        return self


@router.post("/context/remember")
def remember_context(body: ExternalMemoryBody, client: dict = Depends(require_scope("context:write"))):
    # A client cannot impersonate another source or overwrite ordinary indexed docs.
    # Content-addressed source makes an identical retry idempotent.
    import hashlib
    digest = hashlib.sha256(body.body.encode("utf-8")).hexdigest()
    source = f"external-brain:{client['client_id']}:{body.kind}:{digest}"
    document_id = get_store().add_document(body.title, body.body, source)
    AuditLogger().log(client["client_id"], client["user"], "personal-context",
                      "context:remember", document_id, "owner_confirmation_asserted",
                      "success", None, {"kind": body.kind, "body_bytes": len(body.body.encode("utf-8"))})
    return {"document_id": document_id, "status": "indexed", "source": source}


@router.get("/context/documents/{document_id}")
def read_context_document(
    document_id: str = Path(pattern=r"^doc_[0-9a-f]{16}$"),
    offset: int = Query(default=0, ge=0, le=1_000_000),
    limit: int = Query(default=12000, ge=1, le=12000),
    client: dict = Depends(require_scope("context:read")),
):
    result = get_store().get_document(document_id, offset, limit)
    if result is None:
        raise HTTPException(404, "Document not found")
    return result

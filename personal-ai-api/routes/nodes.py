"""Authenticated node inventory and outbound node enrollment/heartbeat routes."""

import json
import os
import secrets
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from control_plane.audit.logger import AuditLogger
from control_plane.storage import get_store

from ..auth.middleware import require_scope

router = APIRouter()


class NodeRegistrationBody(BaseModel):
    node_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    hostname: str = Field(default="unknown", max_length=255)
    architecture: str = Field(default="unknown", max_length=80)
    ram_mb: int = Field(default=0, ge=0, le=1048576)
    tier: str = Field(default="worker", max_length=80)
    capabilities: list[str] = Field(default_factory=list, max_length=64)
    tailscale_ip: str | None = Field(default=None, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def limit_metadata(self):
        if len(json.dumps(self.metadata, default=str)) > 16384:
            raise ValueError("node metadata exceeds 16 KiB")
        return self


class TaskResultBody(BaseModel):
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = Field(default=None, max_length=2048)

    @model_validator(mode="after")
    def limit_result(self):
        if len(json.dumps(self.result, default=str)) > 524288:
            raise ValueError("task result exceeds 512 KiB")
        return self


def _node_token(node_id: str, authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Node bearer token required")
    token = authorization[7:].strip()
    if not get_store().verify_node_token(node_id, token):
        raise HTTPException(401, "Invalid node credential")
    return token


@router.get("/nodes")
def list_nodes(client: dict = Depends(require_scope("nodes:read"))):
    return {"nodes": get_store().list_nodes()}


@router.get("/nodes/{node_id}")
def get_node(node_id: str, client: dict = Depends(require_scope("nodes:read"))):
    node = get_store().get_node(node_id)
    if not node:
        raise HTTPException(404, "Node not registered")
    return node


@router.delete("/nodes/{node_id}")
def revoke_node(
    node_id: str, request: Request, client: dict = Depends(require_scope("nodes:admin"))
):
    if not get_store().revoke_node(node_id):
        raise HTTPException(404, "Node not registered")
    AuditLogger().log(
        client["client_id"],
        client["user"],
        node_id,
        "nodes:revoke",
        node_id,
        "not_required",
        "success",
        request.client.host if request.client else None,
    )
    return {"node_id": node_id, "status": "revoked"}


@router.post("/nodes/register")
def register_node(
    body: NodeRegistrationBody,
    request: Request,
    x_node_enrollment_token: str | None = Header(default=None),
):
    expected = os.environ.get("PAI_NODE_ENROLLMENT_TOKEN", "")
    if (
        not expected
        or not x_node_enrollment_token
        or not secrets.compare_digest(expected, x_node_enrollment_token)
    ):
        raise HTTPException(401, "Invalid node enrollment credential")
    store = get_store()
    node_token = "pai_node_" + secrets.token_urlsafe(40)
    store.register_node(body.model_dump(), node_token=node_token)
    AuditLogger(store=store).log(
        "node-enrollment",
        body.node_id,
        body.node_id,
        "nodes:register",
        body.node_id,
        "not_required",
        "success",
        request.client.host if request.client else None,
    )
    return {
        "node_id": body.node_id,
        "node_token": node_token,
        "message": "Store this token securely; it is only returned once.",
    }


@router.post("/nodes/{node_id}/heartbeat")
def node_heartbeat(
    node_id: str,
    metadata: dict[str, Any],
    authorization: str | None = Header(default=None),
):
    _node_token(node_id, authorization)
    if len(json.dumps(metadata, default=str)) > 16384:
        raise HTTPException(413, "heartbeat metadata exceeds 16 KiB")
    if not get_store().heartbeat(node_id, metadata):
        raise HTTPException(404, "Node not registered")
    return {"status": "ok", "node_id": node_id}


@router.post("/nodes/{node_id}/tasks/next")
def claim_node_task(node_id: str, authorization: str | None = Header(default=None)):
    _node_token(node_id, authorization)
    task = get_store().claim_next_task(node_id)
    return {"task": task}


@router.post("/nodes/{node_id}/tasks/{task_id}/result")
def report_task_result(
    node_id: str,
    task_id: str,
    body: TaskResultBody,
    request: Request,
    authorization: str | None = Header(default=None),
):
    _node_token(node_id, authorization)
    task = get_store().get_task(task_id)
    if not task or task["target_node"] != node_id:
        raise HTTPException(404, "Task not found for this node")
    if task["status"] != "running":
        raise HTTPException(409, "Task is not running")
    result = body.result
    error = body.error
    if not get_store().finish_task(task_id, result, error):
        raise HTTPException(409, "Task result could not be recorded")
    AuditLogger().log(
        task["client_id"],
        task["user_identity"],
        node_id,
        task["operation"],
        task["payload"].get("resource", ""),
        "approved"
        if task["approved"]
        else ("not_required" if not task["requires_approval"] else "pending"),
        "failed"
        if error or result.get("returncode", 0) not in (0, None)
        else "success",
        request.client.host if request.client else None,
        {
            "task_id": task_id,
            "returncode": result.get("returncode"),
            "stdout_bytes": len(str(result.get("stdout", "")).encode("utf-8")),
            "stderr_bytes": len(str(result.get("stderr", "")).encode("utf-8")),
            "error_present": bool(error),
        },
    )
    return {"status": "recorded", "task": get_store().get_task(task_id)}

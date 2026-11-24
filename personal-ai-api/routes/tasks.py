"""Task submission, approval, and status endpoints."""

import json
import secrets
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from control_plane.audit.logger import AuditLogger
from control_plane.authorization.scopes import ScopeValidator
from control_plane.storage import get_store

from ..auth.middleware import get_current_client, require_scope

router = APIRouter()


class TaskCreate(BaseModel):
    target_node: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    operation: str = Field(min_length=1, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)
    required_scope: str | None = None

    @model_validator(mode="after")
    def limit_payload(self):
        if len(json.dumps(self.payload, default=str)) > 32768:
            raise ValueError("task payload exceeds 32 KiB")
        return self


def _required_scope(operation: str, requested: str | None) -> str:
    mapping = {
        "exec": "terminal:execute",
        "shell": "terminal:execute",
        "service_status": "nodes:read",
        "service_restart": "services:manage",
    }
    required = mapping.get(operation)
    if not required:
        raise HTTPException(400, f"Unsupported operation: {operation}")
    if requested and requested != required:
        raise HTTPException(400, "required_scope does not match operation policy")
    return required


@router.post("/tasks", status_code=202)
def submit_task(
    body: TaskCreate, request: Request, client: dict = Depends(get_current_client)
):
    required = _required_scope(body.operation, body.required_scope)
    if not ScopeValidator.has_scope(client["scopes"], required):
        raise HTTPException(403, f"Operation requires {required}")
    if not get_store().get_node(body.target_node):
        raise HTTPException(404, f"Target node '{body.target_node}' is not registered")
    task_id = "task_" + secrets.token_hex(12)
    needs_approval = ScopeValidator.requires_explicit_approval(
        body.operation
    ) or ScopeValidator.requires_payload_approval(body.operation, body.payload)
    get_store().create_task(
        {
            "task_id": task_id,
            "target_node": body.target_node,
            "operation": body.operation,
            "payload": body.payload,
            "required_scope": required,
            "client_id": client["client_id"],
            "user_identity": client["user"],
            "requires_approval": needs_approval,
        }
    )
    AuditLogger().log(
        client["client_id"],
        client["user"],
        body.target_node,
        f"tasks:submit:{body.operation}",
        body.payload.get("resource", ""),
        "required" if needs_approval else "not_required",
        "approval_required" if needs_approval else "queued",
        request.client.host if request.client else None,
        {"task_id": task_id},
    )
    return get_store().get_task(task_id)


@router.get("/tasks/pending-approval")
def list_pending_approval(
    limit: int = 50, client: dict = Depends(require_scope("tasks:approve"))
):
    return {"tasks": get_store().list_pending_approval(limit)}


@router.get("/tasks/{task_id}")
def get_task(task_id: str, client: dict = Depends(get_current_client)):
    task = get_store().get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if (
        task["client_id"] != client["client_id"]
        and "nodes:admin" not in client["scopes"]
    ):
        raise HTTPException(403, "Task belongs to another client")
    return task


@router.post("/tasks/{task_id}/approve")
def approve_task(
    task_id: str,
    request: Request,
    client: dict = Depends(require_scope("tasks:approve")),
):
    task = get_store().get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if not task["requires_approval"] or task["status"] != "approval_required":
        raise HTTPException(409, "Task is not awaiting approval")
    if not get_store().approve_task(task_id):
        raise HTTPException(409, "Approval could not be recorded")
    AuditLogger().log(
        client["client_id"],
        client["user"],
        task["target_node"],
        "tasks:approve",
        task_id,
        "approved",
        "queued",
        request.client.host if request.client else None,
    )
    return get_store().get_task(task_id)

"""End-to-end local API lifecycle test; no Pi or external services required."""

from fastapi.testclient import TestClient


def test_api_node_task_approval_and_context_lifecycle(tmp_path, monkeypatch):
    db_path = str(tmp_path / "api.sqlite3")
    monkeypatch.setenv("PAI_DB_PATH", db_path)
    monkeypatch.setenv("PAI_BOOTSTRAP_TOKEN", "test-admin-token")
    monkeypatch.setenv("PAI_NODE_ENROLLMENT_TOKEN", "test-enrollment-token")

    import personal_ai_api.auth.middleware as middleware
    from control_plane.storage import get_store

    previous_store = middleware.token_manager.store
    store = get_store()
    middleware.token_manager.store = store

    from personal_ai_api.server.app import app

    try:
        with TestClient(app) as client:
            admin = {"Authorization": "Bearer test-admin-token"}
            assert client.get("/health").status_code == 200
            assert client.get("/v1/nodes").status_code == 401

            registration = client.post(
                "/v1/nodes/register",
                headers={"X-Node-Enrollment-Token": "test-enrollment-token"},
                json={
                    "node_id": "pi5",
                    "hostname": "raspberrypi",
                    "architecture": "aarch64",
                    "ram_mb": 4096,
                    "tier": "primary_worker",
                    "capabilities": ["terminal"],
                },
            )
            assert registration.status_code == 200
            node_token = registration.json()["node_token"]
            assert (
                client.get("/v1/nodes", headers=admin).json()["nodes"][0]["node_id"]
                == "pi5"
            )

            submitted = client.post(
                "/v1/tasks",
                headers=admin,
                json={
                    "target_node": "pi5",
                    "operation": "shell",
                    "payload": {"command": "echo approved"},
                },
            )
            assert submitted.status_code == 202
            task_id = submitted.json()["task_id"]
            assert submitted.json()["status"] == "approval_required"
            pending = client.get("/v1/tasks/pending-approval", headers=admin)
            assert (
                pending.status_code == 200
                and pending.json()["tasks"][0]["task_id"] == task_id
            )

            approved = client.post(f"/v1/tasks/{task_id}/approve", headers=admin)
            assert approved.status_code == 200 and approved.json()["status"] == "queued"

            node_headers = {"Authorization": f"Bearer {node_token}"}
            assert (
                client.post(
                    "/v1/nodes/pi5/heartbeat",
                    headers=node_headers,
                    json={"cpu_count": 4},
                ).status_code
                == 200
            )
            claimed = client.post(
                "/v1/nodes/pi5/tasks/next", headers=node_headers
            ).json()["task"]
            assert claimed["task_id"] == task_id and claimed["approved"] is True
            reported = client.post(
                f"/v1/nodes/pi5/tasks/{task_id}/result",
                headers=node_headers,
                json={"result": {"stdout": "approved", "returncode": 0}},
            )
            assert reported.status_code == 200
            assert reported.json()["task"]["status"] == "completed"

            indexer = store.issue_token(
                "context-indexer", "indexer", "owner", {"context:write"}
            )
            indexed = client.post(
                "/v1/context/index",
                headers={"Authorization": f"Bearer {indexer}"},
                json={
                    "title": "Pi runbook",
                    "body": "The Raspberry Pi 5 hosts Hermes and Beeper.",
                    "source": "runbook.md",
                },
            )
            assert indexed.status_code == 200
            context = client.post(
                "/v1/context/query", headers=admin, json={"query": "Raspberry Pi"}
            )
            assert context.status_code == 200 and context.json()["results"]
            assert (
                client.post(
                    "/v1/context/query",
                    headers={"Authorization": f"Bearer {indexer}"},
                    json={"query": "Pi"},
                ).status_code
                == 403
            )
            assert store.verify_audit_chain()

            limited = store.issue_token("read-only", "mcp", "owner", {"context:read"})
            assert (
                client.get(
                    "/v1/nodes", headers={"Authorization": f"Bearer {limited}"}
                ).status_code
                == 403
            )
            revoked = client.delete("/v1/nodes/pi5", headers=admin)
            assert revoked.status_code == 200
            assert (
                client.post(
                    "/v1/nodes/pi5/heartbeat", headers=node_headers, json={}
                ).status_code
                == 401
            )
    finally:
        middleware.token_manager.store = previous_store

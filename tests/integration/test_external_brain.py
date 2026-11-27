from fastapi.testclient import TestClient


def test_external_brain_shared_memory_and_approval(tmp_path, monkeypatch):
    monkeypatch.setenv("PAI_DB_PATH", str(tmp_path / "external.sqlite3"))
    monkeypatch.setenv("PAI_BOOTSTRAP_TOKEN", "external-test-admin")
    monkeypatch.setenv("PAI_NODE_ENROLLMENT_TOKEN", "external-enrollment")
    from control_plane.storage import get_store
    import personal_ai_api.auth.middleware as middleware
    from personal_ai_api.server.app import app
    store = get_store()
    monkeypatch.setattr(middleware.token_manager, "store", store)
    writer = store.issue_token("chatgpt-demo", "external-brain", "owner", {"context:write", "context:read", "nodes:read", "terminal:execute"})
    reader = store.issue_token("hermes-demo", "mcp", "owner", {"context:read"})
    headers = {"Authorization": "Bearer " + writer}
    reader_headers = {"Authorization": "Bearer " + reader}
    with TestClient(app) as c:
        body = {"title": "Decision", "body": "Use shared memory. " * 1000, "owner_confirmed": True}
        assert c.post("/v1/context/remember", headers=headers, json={**body, "owner_confirmed": False}).status_code == 422
        assert c.post("/v1/context/remember", headers=reader_headers, json=body).status_code == 403
        assert c.post("/v1/context/index", headers=headers, json={"title":"test","body":"test","source":"manual"}).status_code == 403
        r = c.post("/v1/context/remember", headers=headers, json=body)
        assert r.status_code == 200, r.text
        doc = r.json()["document_id"]
        assert c.post("/v1/context/remember", headers=headers, json=body).json()["document_id"] == doc
        matches = c.post("/v1/context/query", headers=reader_headers, json={"query": "shared memory"}).json()["results"]
        assert doc in {m["document_id"] for m in matches}
        assert c.get(f"/v1/context/documents/{doc}").status_code == 401
        first = c.get(f"/v1/context/documents/{doc}", headers=reader_headers).json()
        second = c.get(f"/v1/context/documents/{doc}?offset={first['next_offset']}", headers=reader_headers).json()
        assert first["body"] + second["body"] == body["body"]
        assert second["next_offset"] is None
        assert c.post("/v1/nodes/register", headers={"X-Node-Enrollment-Token": "external-enrollment"}, json={"node_id": "pi5", "hostname": "raspberrypi", "architecture": "aarch64", "ram_mb": 4096, "tier": "primary_worker", "capabilities": ["terminal"]}).status_code == 200
        def submit(argv):
            return c.post("/v1/tasks", headers=headers, json={"target_node": "pi5", "operation": "exec", "payload": {"argv": argv}}).json()
        assert submit(["hostname"])["status"] == "queued"
        task = submit(["touch", "/tmp/test"])
        assert task["status"] == "approval_required"
        assert c.post(f"/v1/tasks/{task['task_id']}/approve", headers=headers).status_code == 403
        assert c.get(f"/v1/tasks/{task['task_id']}", headers=reader_headers).status_code == 403
        assert store.verify_audit_chain()

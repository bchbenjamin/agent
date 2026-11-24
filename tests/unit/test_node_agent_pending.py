"""Node-agent durability tests."""

import pytest

from node_agent.core.agent import NodeAgent


def test_pending_task_result_survives_api_restart(tmp_path, monkeypatch):
    import httpx

    monkeypatch.setenv("PAI_NODE_PENDING_DIR", str(tmp_path / "pending"))
    state = {"next_calls": 0, "result_calls": 0}

    def handler(request):
        if request.url.path.endswith("/heartbeat"):
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path.endswith("/tasks/next"):
            state["next_calls"] += 1
            task = None
            if state["next_calls"] == 1:
                task = {
                    "task_id": "task_durable",
                    "operation": "exec",
                    "payload": {"argv": ["/bin/echo", "durable"]},
                    "approved": False,
                }
            return httpx.Response(200, json={"task": task})
        if request.url.path.endswith("/result"):
            state["result_calls"] += 1
            if state["result_calls"] == 1:
                return httpx.Response(503, json={"detail": "API restarting"})
            return httpx.Response(200, json={"status": "recorded"})
        raise AssertionError(f"Unexpected request: {request.url}")

    client = httpx.Client(transport=httpx.MockTransport(handler), trust_env=False)
    agent = NodeAgent("pi5", "http://pai.test", "node-test-token", http_client=client)
    with pytest.raises(httpx.HTTPStatusError):
        agent.run_once()
    pending = tmp_path / "pending" / "task_durable.json"
    assert pending.exists()
    assert agent.run_once() is False
    assert not pending.exists()
    assert state["result_calls"] == 2
    client.close()

"""Persistence, credential and audit-chain regression tests."""

from control_plane.authorization.scopes import ScopeValidator
from control_plane.storage import SQLiteStore
from node_agent.execution.runner import TaskRunner


def test_token_hash_only_and_persistent_revocation(tmp_path):
    import stat

    path = tmp_path / "pai.sqlite3"
    store = SQLiteStore(str(path))
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    token = store.issue_token("client-a", "mcp", "owner", {"nodes:read"})
    with store.connect() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("UPDATE clients SET revoked=0 WHERE client_id='client-a'")
        for sidecar in (
            path.with_name(path.name + "-wal"),
            path.with_name(path.name + "-shm"),
        ):
            if sidecar.exists():
                assert stat.S_IMODE(sidecar.stat().st_mode) == 0o600
    assert store.verify_token(token)["client_id"] == "client-a"
    assert token.encode() not in path.read_bytes()
    reopened = SQLiteStore(str(path))
    assert reopened.verify_token(token)["scopes"] == {"nodes:read"}
    assert reopened.revoke_token(token)
    assert reopened.verify_token(token) is None


def test_node_credentials_can_be_revoked(tmp_path):
    store = SQLiteStore(str(tmp_path / "pai.sqlite3"))
    store.register_node(
        {
            "node_id": "pi5",
            "hostname": "pi5",
            "architecture": "aarch64",
            "ram_mb": 4096,
            "tier": "primary_worker",
        },
        "node-secret",
    )
    assert store.verify_node_token("pi5", "node-secret")
    assert store.revoke_node("pi5")
    assert not store.verify_node_token("pi5", "node-secret")
    assert store.get_node("pi5")["status"] == "offline"


def test_node_registration_queue_and_approval_lifecycle(tmp_path):
    store = SQLiteStore(str(tmp_path / "pai.sqlite3"))
    node_token = "pai_node_test_secret"
    store.register_node(
        {
            "node_id": "pi5",
            "hostname": "raspberrypi",
            "architecture": "aarch64",
            "ram_mb": 4096,
            "tier": "primary_worker",
            "capabilities": ["terminal"],
        },
        node_token,
    )
    assert store.verify_node_token("pi5", node_token)
    assert store.heartbeat("pi5", {"cpu_count": 4})
    store.create_task(
        {
            "task_id": "task-1",
            "target_node": "pi5",
            "operation": "shell",
            "payload": {"command": "echo ok"},
            "required_scope": "terminal:execute",
            "client_id": "mcp",
            "user_identity": "owner",
            "requires_approval": True,
        }
    )
    assert store.claim_next_task("pi5") is None
    assert store.approve_task("task-1")
    task = store.claim_next_task("pi5")
    assert task["status"] == "running" and task["approved"] is True
    assert store.finish_task("task-1", {"stdout": "ok", "returncode": 0})
    assert store.get_task("task-1")["status"] == "completed"


def test_expired_task_lease_is_requeued(tmp_path):
    from datetime import datetime, timedelta, timezone

    store = SQLiteStore(str(tmp_path / "pai.sqlite3"))
    store.register_node(
        {
            "node_id": "pi5",
            "hostname": "pi5",
            "architecture": "aarch64",
            "ram_mb": 4096,
            "tier": "primary_worker",
        },
        "node-secret",
    )
    store.create_task(
        {
            "task_id": "task-lease",
            "target_node": "pi5",
            "operation": "exec",
            "payload": {"argv": ["/bin/echo", "lease"]},
            "required_scope": "terminal:execute",
            "client_id": "hermes",
            "user_identity": "owner",
            "requires_approval": False,
        }
    )
    assert store.claim_next_task("pi5")["status"] == "running"
    expired = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    with store.connect() as db:
        db.execute(
            "UPDATE tasks SET claimed_at=? WHERE task_id='task-lease'", (expired,)
        )
    reclaimed = store.claim_next_task("pi5")
    assert reclaimed["task_id"] == "task-lease" and reclaimed["status"] == "running"


def test_audit_chain_detects_tampering(tmp_path):
    store = SQLiteStore(str(tmp_path / "pai.sqlite3"))
    store.append_audit({"operation": "nodes:register", "result": "success"})
    store.append_audit({"operation": "tasks:submit", "result": "queued"})
    assert store.verify_audit_chain()
    with store.connect() as db:
        db.execute("UPDATE audit_events SET result='tampered' WHERE seq=1")
    assert not store.verify_audit_chain()


def test_payload_sensitive_commands_require_approval():
    assert ScopeValidator.requires_payload_approval(
        "exec", {"argv": ["wipefs", "/dev/sda"]}
    )
    assert not ScopeValidator.requires_payload_approval("exec", {"argv": ["ls", "-la"]})


def test_runner_uses_argv_and_blocks_sensitive_operations():
    runner = TaskRunner()
    assert runner.run_command(["/bin/echo", "ok"])["stdout"].strip() == "ok"
    denied = runner.run_command("wipefs /dev/sda")
    assert denied["returncode"] == 1
    assert "rejected" in denied["error"]
    assert (
        runner.run_command(["/bin/bash", "-lc", "sudo id"], approved=True)["returncode"]
        == 1
    )
    assert runner.run_shell("sudo id", approved=True)["returncode"] == 1
    assert runner.run_command(["find", "/home", "-delete"])["returncode"] == 1
    assert runner.run_command(["apt-get", "install", "package"])["returncode"] == 1
    assert runner.run_shell("echo approved", approved=False)["returncode"] == 126


def test_runner_uses_configured_user_helper(tmp_path, monkeypatch):
    helper = tmp_path / "helper"
    helper.write_text('#!/bin/sh\nshift 2\nexec "$@"\n', encoding="utf-8")
    helper.chmod(0o755)
    monkeypatch.setenv("PAI_EXECUTION_HELPER", str(helper))
    monkeypatch.setenv("PAI_NODE_AGENT_REQUIRE_USER_HELPER", "true")
    runner = TaskRunner()
    assert (
        runner.run_command(["/bin/echo", "through-helper"])["stdout"].strip()
        == "through-helper"
    )


def test_runner_enforces_output_limit_without_limiting_file_writes(tmp_path):
    runner = TaskRunner()
    result = runner.run_command(["/usr/bin/yes"], timeout=2)
    assert len(result.get("stdout", "")) <= TaskRunner.MAX_OUTPUT + 64

    target = tmp_path / "larger-than-output-cap.bin"
    write_result = runner.run_command(
        ["/usr/bin/python3", "-c", f"open({str(target)!r}, 'wb').write(b'x' * 100000)"],
        timeout=5,
        approved=True,
    )
    assert write_result["returncode"] == 0
    assert target.stat().st_size == 100000

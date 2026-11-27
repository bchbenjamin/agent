import importlib.util
from pathlib import Path
import sqlite3
import pytest
from control_plane.storage import SQLiteStore

path = Path(__file__).resolve().parents[2] / "deployment/backup/control-plane-snapshot.py"
spec = importlib.util.spec_from_file_location("snapshot_helper", path)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

def test_snapshot_preserves_context_and_client_identity(tmp_path):
    original = tmp_path / "original.sqlite3"
    copy = tmp_path / "copy.sqlite3"
    store = SQLiteStore(str(original))
    token = store.issue_token("migration-client", "external-brain", "owner", {"context:read"})
    doc = store.add_document("synthetic", "migration context", "test")
    assert helper.snapshot(original, copy, quiescent=True) == {}
    assert copy.stat().st_mode & 0o777 == 0o600
    restored = SQLiteStore(str(copy))
    assert restored.verify_token(token)["client_id"] == "migration-client"
    assert restored.get_document(doc)["body"] == "migration context"
    assert restored.verify_audit_chain()
    with pytest.raises(FileExistsError):
        helper.snapshot(original, copy)

def test_snapshot_rejects_incompatible_database(tmp_path):
    original = tmp_path / "wrong.sqlite3"
    with sqlite3.connect(original) as c:
        c.execute("CREATE TABLE unrelated (id INT)")
    copy = tmp_path / "copy.sqlite3"
    with pytest.raises(ValueError):
        helper.snapshot(original, copy)
    assert not copy.exists()

def test_migration_rejects_queued_tasks(tmp_path):
    store = SQLiteStore(str(tmp_path / "source.sqlite3"))
    store.create_task({"task_id":"task_test","target_node":"pi5","operation":"exec",
        "payload":{"argv":["hostname"]},"required_scope":"terminal:execute",
        "client_id":"test","user_identity":"owner","requires_approval":False})
    with pytest.raises(ValueError, match="outstanding tasks"):
        helper.snapshot(Path(store.path), tmp_path / "copy.sqlite3", quiescent=True)
    assert helper.snapshot(Path(store.path), tmp_path / "ordinary.sqlite3") == {"queued":1}

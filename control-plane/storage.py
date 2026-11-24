"""SQLite persistence for Personal AI control-plane state.

The database stores credential hashes only. Set PAI_DB_PATH to a persistent,
private filesystem location in production.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

ZERO_HASH = "0" * 64


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class SQLiteStore:
    def __init__(self, path: str | None = None):
        configured = path or os.environ.get("PAI_DB_PATH")
        self.path = configured or str(
            Path.home() / ".local/share/personal-ai/pai.sqlite3"
        )
        if self.path != ":memory:":
            self.path = str(Path(self.path).expanduser())
        if self.path != ":memory:":
            Path(self.path).expanduser().parent.mkdir(
                parents=True, exist_ok=True, mode=0o700
            )
        self._lock = threading.RLock()
        self._initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=15000")
        try:
            yield conn
        finally:
            conn.close()

    def _initialize(self) -> None:
        with self._lock, self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
            CREATE TABLE IF NOT EXISTS clients (
              client_id TEXT PRIMARY KEY, client_type TEXT NOT NULL, user_identity TEXT NOT NULL,
              created_at TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS tokens (
              token_hash TEXT PRIMARY KEY, client_id TEXT NOT NULL REFERENCES clients(client_id),
              scopes_json TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT,
              revoked INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_tokens_client ON tokens(client_id);
            CREATE TABLE IF NOT EXISTS nodes (
              node_id TEXT PRIMARY KEY, hostname TEXT NOT NULL, architecture TEXT NOT NULL,
              ram_mb INTEGER NOT NULL, tier TEXT NOT NULL, capabilities_json TEXT NOT NULL,
              tailscale_ip TEXT, node_token_hash TEXT, registered_at TEXT NOT NULL,
              last_seen TEXT, metadata_json TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS tasks (
              task_id TEXT PRIMARY KEY, target_node TEXT NOT NULL, operation TEXT NOT NULL,
              payload_json TEXT NOT NULL, required_scope TEXT NOT NULL, client_id TEXT NOT NULL,
              user_identity TEXT NOT NULL, status TEXT NOT NULL, requires_approval INTEGER NOT NULL,
              approved INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              result_json TEXT, claimed_at TEXT, completed_at TEXT, error TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_tasks_queue ON tasks(target_node, status, created_at);
            CREATE TABLE IF NOT EXISTS audit_events (
              seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL,
              timestamp TEXT NOT NULL, client_id TEXT NOT NULL, user_identity TEXT NOT NULL,
              target_node TEXT NOT NULL, operation TEXT NOT NULL, target_resource TEXT NOT NULL,
              approval_status TEXT NOT NULL, result TEXT NOT NULL, client_ip TEXT,
              details_json TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS context_documents (
              document_id TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL,
              source TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            """)
        if self.path != ":memory:" and os.path.exists(self.path):
            os.chmod(self.path, 0o600)

    @staticmethod
    def token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def issue_token(
        self, client_id: str, client_type: str, user: str, scopes: set[str]
    ) -> str:
        raw = f"pai_{client_type}_{secrets.token_urlsafe(32)}"
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT INTO clients(client_id,client_type,user_identity,created_at,revoked) VALUES(?,?,?,?,0) "
                "ON CONFLICT(client_id) DO UPDATE SET client_type=excluded.client_type,user_identity=excluded.user_identity,revoked=0",
                (client_id, client_type, user, utcnow()),
            )
            db.execute(
                "INSERT INTO tokens(token_hash,client_id,scopes_json,created_at) VALUES(?,?,?,?)",
                (
                    self.token_hash(raw),
                    client_id,
                    canonical_json(sorted(scopes)),
                    utcnow(),
                ),
            )
            db.commit()
        return raw

    def verify_token(self, token: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute(
                """SELECT t.client_id,t.scopes_json,c.client_type,c.user_identity
                   FROM tokens t JOIN clients c ON c.client_id=t.client_id
                   WHERE t.token_hash=? AND t.revoked=0 AND c.revoked=0
                     AND (t.expires_at IS NULL OR t.expires_at > ?)""",
                (self.token_hash(token), utcnow()),
            ).fetchone()
        if not row:
            return None
        return {
            "client_id": row["client_id"],
            "client_type": row["client_type"],
            "user": row["user_identity"],
            "scopes": set(json.loads(row["scopes_json"])),
        }

    def revoke_token(self, token: str) -> bool:
        with self.connect() as db:
            cur = db.execute(
                "UPDATE tokens SET revoked=1 WHERE token_hash=?",
                (self.token_hash(token),),
            )
            return cur.rowcount > 0

    def revoke_client(self, client_id: str) -> bool:
        with self.connect() as db:
            cur = db.execute(
                "UPDATE clients SET revoked=1 WHERE client_id=?", (client_id,)
            )
            return cur.rowcount > 0

    def register_node(
        self, data: dict[str, Any], node_token: str | None = None
    ) -> None:
        now = utcnow()
        token_hash = self.token_hash(node_token) if node_token else None
        with self.connect() as db:
            db.execute(
                """INSERT INTO nodes(node_id,hostname,architecture,ram_mb,tier,capabilities_json,
                   tailscale_ip,node_token_hash,registered_at,last_seen,metadata_json)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(node_id) DO UPDATE SET hostname=excluded.hostname,
                   architecture=excluded.architecture,ram_mb=excluded.ram_mb,tier=excluded.tier,
                   capabilities_json=excluded.capabilities_json,tailscale_ip=excluded.tailscale_ip,
                   node_token_hash=COALESCE(excluded.node_token_hash,nodes.node_token_hash),
                   last_seen=excluded.last_seen,metadata_json=excluded.metadata_json""",
                (
                    data["node_id"],
                    data.get("hostname", data["node_id"]),
                    data.get("architecture", "unknown"),
                    int(data.get("ram_mb", 0)),
                    data.get("tier", "worker"),
                    canonical_json(data.get("capabilities", [])),
                    data.get("tailscale_ip"),
                    token_hash,
                    now,
                    now,
                    canonical_json(data.get("metadata", {})),
                ),
            )

    def verify_node_token(self, node_id: str, token: str) -> bool:
        with self.connect() as db:
            row = db.execute(
                "SELECT node_token_hash FROM nodes WHERE node_id=?", (node_id,)
            ).fetchone()
        return bool(
            row
            and row["node_token_hash"]
            and secrets.compare_digest(row["node_token_hash"], self.token_hash(token))
        )

    def revoke_node(self, node_id: str) -> bool:
        with self.connect() as db:
            cur = db.execute(
                "UPDATE nodes SET node_token_hash=NULL,last_seen=NULL WHERE node_id=?",
                (node_id,),
            )
            return cur.rowcount > 0

    def heartbeat(self, node_id: str, metadata: dict[str, Any] | None = None) -> bool:
        with self.connect() as db:
            cur = db.execute(
                "UPDATE nodes SET last_seen=?,metadata_json=?,tailscale_ip=COALESCE(?,tailscale_ip) WHERE node_id=?",
                (
                    utcnow(),
                    canonical_json(metadata or {}),
                    (metadata or {}).get("tailscale_ip"),
                    node_id,
                ),
            )
            return cur.rowcount > 0

    def list_nodes(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM nodes ORDER BY node_id").fetchall()
        now = datetime.now(timezone.utc).timestamp()
        out = []
        for row in rows:
            last = row["last_seen"]
            try:
                age = now - datetime.fromisoformat(last).timestamp() if last else None
            except ValueError:
                age = None
            out.append(
                {
                    "node_id": row["node_id"],
                    "hostname": row["hostname"],
                    "architecture": row["architecture"],
                    "ram_mb": row["ram_mb"],
                    "tier": row["tier"],
                    "capabilities": json.loads(row["capabilities_json"]),
                    "tailscale_ip": row["tailscale_ip"],
                    "registered_at": row["registered_at"],
                    "last_seen": last,
                    "status": "online" if age is not None and age <= 120 else "offline",
                    "metadata": json.loads(row["metadata_json"]),
                }
            )
        return out

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        return next((n for n in self.list_nodes() if n["node_id"] == node_id), None)

    def create_task(self, task: dict[str, Any]) -> None:
        now = utcnow()
        with self.connect() as db:
            db.execute(
                """INSERT INTO tasks(task_id,target_node,operation,payload_json,required_scope,client_id,
                   user_identity,status,requires_approval,approved,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    task["task_id"],
                    task["target_node"],
                    task["operation"],
                    canonical_json(task.get("payload", {})),
                    task["required_scope"],
                    task["client_id"],
                    task["user_identity"],
                    "approval_required" if task.get("requires_approval") else "queued",
                    int(task.get("requires_approval", False)),
                    int(task.get("approved", False)),
                    now,
                    now,
                ),
            )

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM tasks WHERE task_id=?", (task_id,)
            ).fetchone()
        return self._task_dict(row) if row else None

    def list_pending_approval(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM tasks WHERE status='approval_required' ORDER BY created_at LIMIT ?",
                (max(1, min(limit, 200)),),
            ).fetchall()
        return [self._task_dict(row) for row in rows]

    @staticmethod
    def _task_dict(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        d["payload"] = json.loads(d.pop("payload_json"))
        d["result"] = json.loads(d.pop("result_json")) if d.get("result_json") else None
        d["requires_approval"] = bool(d["requires_approval"])
        d["approved"] = bool(d["approved"])
        return d

    def approve_task(self, task_id: str) -> bool:
        with self.connect() as db:
            cur = db.execute(
                "UPDATE tasks SET approved=1,status='queued',updated_at=? WHERE task_id=? AND status='approval_required'",
                (utcnow(), task_id),
            )
            return cur.rowcount > 0

    def claim_next_task(self, node_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            # Recover work abandoned by a crashed/rebooted node. The runner's
            # hard execution timeout is 120s; a 5-minute lease leaves margin.
            lease_cutoff = (
                datetime.now(timezone.utc) - timedelta(minutes=5)
            ).isoformat()
            db.execute(
                "UPDATE tasks SET status='queued',claimed_at=NULL,updated_at=? "
                "WHERE target_node=? AND status='running' AND claimed_at < ?",
                (utcnow(), node_id, lease_cutoff),
            )
            row = db.execute(
                "SELECT * FROM tasks WHERE target_node=? AND status='queued' AND (requires_approval=0 OR approved=1) "
                "ORDER BY created_at LIMIT 1",
                (node_id,),
            ).fetchone()
            if not row:
                db.commit()
                return None
            db.execute(
                "UPDATE tasks SET status='running',claimed_at=?,updated_at=? WHERE task_id=?",
                (utcnow(), utcnow(), row["task_id"]),
            )
            db.commit()
            return self.get_task(row["task_id"])

    def finish_task(
        self, task_id: str, result: dict[str, Any], error: str | None = None
    ) -> bool:
        status = (
            "failed"
            if error or result.get("returncode", 0) not in (0, None)
            else "completed"
        )
        with self.connect() as db:
            cur = db.execute(
                "UPDATE tasks SET status=?,result_json=?,error=?,updated_at=?,completed_at=? WHERE task_id=? AND status='running'",
                (status, canonical_json(result), error, utcnow(), utcnow(), task_id),
            )
            return cur.rowcount > 0

    def append_audit(self, event: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            prev = db.execute(
                "SELECT event_hash FROM audit_events ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            previous_hash = prev["event_hash"] if prev else ZERO_HASH
            timestamp = utcnow()
            body = {
                "event_id": "evt_" + secrets.token_hex(8),
                "timestamp": timestamp,
                "client_id": event.get("client_id", "system"),
                "user_identity": event.get("user_identity", "system"),
                "target_node": event.get("target_node", ""),
                "operation": event["operation"],
                "target_resource": event.get("target_resource", ""),
                "approval_status": event.get("approval_status", "not_required"),
                "result": event.get("result", "unknown"),
                "client_ip": event.get("client_ip"),
                "details": event.get("details", {}),
            }
            event_hash = hashlib.sha256(
                (previous_hash + canonical_json(body)).encode()
            ).hexdigest()
            record = {**body, "previous_hash": previous_hash, "event_hash": event_hash}
            db.execute(
                """INSERT INTO audit_events(event_id,timestamp,client_id,user_identity,target_node,operation,
                   target_resource,approval_status,result,client_ip,details_json,previous_hash,event_hash)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    record["event_id"],
                    timestamp,
                    body["client_id"],
                    body["user_identity"],
                    body["target_node"],
                    body["operation"],
                    body["target_resource"],
                    body["approval_status"],
                    body["result"],
                    body["client_ip"],
                    canonical_json(body["details"]),
                    previous_hash,
                    event_hash,
                ),
            )
            db.commit()
        return record

    def verify_audit_chain(self) -> bool:
        previous = ZERO_HASH
        with self.connect() as db:
            rows = db.execute("SELECT * FROM audit_events ORDER BY seq").fetchall()
        for row in rows:
            body = {
                "event_id": row["event_id"],
                "timestamp": row["timestamp"],
                "client_id": row["client_id"],
                "user_identity": row["user_identity"],
                "target_node": row["target_node"],
                "operation": row["operation"],
                "target_resource": row["target_resource"],
                "approval_status": row["approval_status"],
                "result": row["result"],
                "client_ip": row["client_ip"],
                "details": json.loads(row["details_json"]),
            }
            digest = hashlib.sha256(
                (previous + canonical_json(body)).encode()
            ).hexdigest()
            if row["previous_hash"] != previous or row["event_hash"] != digest:
                return False
            previous = digest
        return True

    def recent_audit(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM audit_events ORDER BY seq DESC LIMIT ?",
                (max(1, min(limit, 500)),),
            ).fetchall()
        return [dict(r) | {"details": json.loads(r["details_json"])} for r in rows]

    def add_document(self, title: str, body: str, source: str = "manual") -> str:
        doc_id = (
            "doc_"
            + hashlib.sha256((source + "\\0" + title).encode("utf-8")).hexdigest()[:16]
        )
        with self.connect() as db:
            db.execute(
                "INSERT INTO context_documents VALUES(?,?,?,?,?) ON CONFLICT(document_id) DO UPDATE SET "
                "title=excluded.title,body=excluded.body,source=excluded.source,updated_at=excluded.updated_at",
                (doc_id, title, body, source, utcnow()),
            )
        return doc_id

    def query_context(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        terms = [t.strip() for t in query.split() if t.strip()]
        if not terms:
            return []
        clauses = " OR ".join(
            ["lower(title) LIKE ? OR lower(body) LIKE ?" for _ in terms]
        )
        params: list[str] = []
        for term in terms:
            needle = f"%{term.lower()}%"
            params.extend([needle, needle])
        with self.connect() as db:
            rows = db.execute(
                f"SELECT document_id,title,body,source,updated_at FROM context_documents WHERE {clauses} ORDER BY updated_at DESC LIMIT ?",
                (*params, max(1, min(limit, 50))),
            ).fetchall()
        return [
            {
                "document_id": r["document_id"],
                "title": r["title"],
                "snippet": r["body"][:1200],
                "source": r["source"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]


_store: SQLiteStore | None = None
_store_path: str | None = None


def get_store() -> SQLiteStore:
    global _store, _store_path
    path = os.environ.get("PAI_DB_PATH")
    if _store is None or path != _store_path:
        _store = SQLiteStore(path)
        _store_path = path
    return _store

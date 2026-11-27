#!/usr/bin/env python3
"""Create/verify a consistent SQLite snapshot; sensitive output stays off Git."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import sqlite3

REQUIRED = {"clients", "tokens", "nodes", "tasks", "audit_events", "context_documents"}

def validate(conn: sqlite3.Connection, *, quiescent: bool = False) -> dict:
    if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise ValueError("Database integrity check failed")
    if conn.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise ValueError("Foreign-key integrity check failed")
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not REQUIRED <= tables:
        raise ValueError("Not a Personal AI control-plane database")
    counts = dict(conn.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status"))
    if quiescent and any(counts.get(s, 0) for s in ("running", "queued", "approval_required")):
        raise ValueError("Drain or reconcile outstanding tasks before migration")
    return counts

def connect_readonly(path: Path) -> sqlite3.Connection:
    if not path.is_file() or path.is_symlink():
        raise ValueError("Expected a regular database file")
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=15)

def verify(path: Path, quiescent: bool = False) -> dict:
    with connect_readonly(path) as conn:
        try:
            return validate(conn, quiescent=quiescent)
        finally:
            conn.close()

def snapshot(source: Path, target: Path, quiescent: bool = False) -> dict:
    if target.exists() or target.is_symlink():
        raise FileExistsError("Refusing to overwrite snapshot")
    if not target.parent.is_dir():
        raise ValueError("Create a protected destination directory first")
    src = connect_readonly(source)
    try:
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        try:
            dst = sqlite3.connect(target, timeout=15)
            try:
                src.backup(dst)
                counts = validate(dst, quiescent=quiescent)
                # Produce a self-contained snapshot, not a database dependent on WAL sidecars.
                dst.execute("PRAGMA journal_mode=DELETE")
                dst.commit()
            finally:
                dst.close()
            os.chmod(target, 0o600)
            return counts
        except BaseException:
            for path in (target, Path(str(target)+"-wal"), Path(str(target)+"-shm"), Path(str(target)+"-journal")):
                path.unlink(missing_ok=True)
            raise
    finally:
        src.close()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    backup = sub.add_parser("snapshot")
    backup.add_argument("source", type=Path)
    backup.add_argument("destination", type=Path)
    check = sub.add_parser("verify")
    check.add_argument("source", type=Path)
    for command in (backup, check):
        command.add_argument("--quiescent", action="store_true")
    args = parser.parse_args()
    if args.command == "snapshot":
        counts = snapshot(args.source, args.destination, args.quiescent)
    else:
        counts = verify(args.source, args.quiescent)
    print("Verified SQLite integrity and schema. Task status counts:", counts)

if __name__ == "__main__":
    os.umask(0o077)
    main()

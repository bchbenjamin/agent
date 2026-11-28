#!/usr/bin/env python3
"""Recover core services only when the verified microSD database exists.

This helper never mounts, repairs, initializes, or writes to the optional SSD.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path
from urllib.request import urlopen

DB = Path("/var/lib/pai-api/control-plane.sqlite3")
ENV = Path("/etc/personal-ai/api.env")


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=20, check=False)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, 124, "", "command timed out")


def _configured_database() -> str | None:
    try:
        for line in ENV.read_text().splitlines():
            if line.startswith("PAI_DB_PATH="):
                return line.partition("=")[2].strip()
    except OSError:
        return None
    return None


def _api_healthy(attempts: int = 20) -> bool:
    for attempt in range(attempts):
        try:
            with urlopen("http://127.0.0.1:8000/health", timeout=2) as response:
                if response.status == 200:
                    return True
        except Exception:
            pass
        if attempt + 1 < attempts:
            time.sleep(1)
    return False


def recover() -> int:
    # Critically, never let the API initialize an empty DB after a missing drive.
    if _configured_database() != str(DB) or not DB.is_file() or DB.is_symlink():
        return 0
    if _run("systemctl", "is-active", "--quiet", "personal-ai-api.service").returncode != 0:
        if _run("systemctl", "start", "personal-ai-api.service").returncode != 0:
            return 1
    if not _api_healthy():
        return 1
    if _run("systemctl", "is-active", "--quiet", "personal-ai-mcp.service").returncode != 0:
        if _run("systemctl", "start", "personal-ai-mcp.service").returncode != 0:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(recover())

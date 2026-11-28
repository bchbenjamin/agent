#!/usr/bin/env python3
"""Restore API/MCP services only after the expected SSD is already mounted."""

from __future__ import annotations

import subprocess
import time
from urllib.request import urlopen

MOUNT = "/mnt/pi_data"
EXPECTED_UUID = "cbdf283b-2951-44de-945e-c082bf87f337"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=20, check=False)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, 124, "", "command timed out")


def _verified_mount() -> bool:
    # Do not mount or fsck a possibly unstable volume from a retry timer.
    # fstab owns mounting; this unit only recovers services after it succeeds.
    result = _run("findmnt", "-n", "-o", "UUID", "--target", MOUNT)
    return result.returncode == 0 and result.stdout.strip() == EXPECTED_UUID


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
    """Return success when storage is absent; retry on the next timer tick."""
    if not _verified_mount():
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

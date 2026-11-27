#!/usr/bin/env python3
"""Prepare one optional integration's env update. Never prints credential values."""
from __future__ import annotations
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import stat
import tempfile

KEYS = {"box": ("MCP_BOX_API_KEY", "PAI_BOX_MCP_TOKEN"),
        "history": ("API_SERVER_KEY", "PAI_HERMES_API_KEY"),
        "beeper": (None, "PAI_BEEPER_MCP_TOKEN")}
SAFE = re.compile(r"[A-Za-z0-9._~+/=-]+")

def dotenv_value(text: str, key: str) -> str:
    matches = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("export "):
            line = line[7:].lstrip()
        lhs, sep, rhs = line.partition("=")
        if sep and lhs.strip() == key:
            parts = shlex.split(rhs, comments=True, posix=True)
            if len(parts) != 1:
                raise ValueError("Invalid credential assignment")
            matches.append(parts[0])
    if len(matches) != 1:
        raise ValueError("Credential absent or ambiguous")
    return matches[0]

def read_token(home: Path, kind: str, now: float) -> str:
    source, _ = KEYS[kind]
    if source:
        token = dotenv_value((home / ".hermes-pi/.env").read_text(), source)
    else:
        data = json.loads((home / ".hermes-pi/mcp-tokens/beeper.json").read_text())
        token = data.get("access_token", "")
        expires = data.get("expires_at")
        if isinstance(expires, str):
            d = datetime.datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if d.tzinfo is None:
                d = d.replace(tzinfo=datetime.timezone.utc)
            expires = d.timestamp()
        if not isinstance(expires, (int, float)) or isinstance(expires, bool) or expires <= now + 60:
            raise ValueError("Beeper token expiry missing or token expired; issue a supported dedicated credential")
    if not isinstance(token, str) or not SAFE.fullmatch(token):
        raise ValueError("Credential absent or unsupported")
    return token

def replace_entry(text: str, key: str, token: str) -> str:
    if not SAFE.fullmatch(token):
        raise ValueError("Unsupported token")
    lines = text.splitlines()
    matches = [i for i, line in enumerate(lines) if line.partition("=")[0].strip() == key]
    if len(matches) > 1:
        raise ValueError("Existing environment contains duplicate assignments")
    if matches:
        lines[matches[0]] = f"{key}={token}"
    else:
        lines.append(f"{key}={token}")
    return "\n".join(lines) + "\n"

def atomic_write(target: Path, data: str, mode: int, gid: int) -> None:
    fd, path = tempfile.mkstemp(prefix=".mcp.env.", dir=target.parent)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chown(path, 0, gid)
        os.chmod(path, mode)
        os.replace(path, target)
    finally:
        if os.path.exists(path):
            os.unlink(path)

def main() -> int:
    import grp, pwd, time
    parser = argparse.ArgumentParser()
    parser.add_argument("integration", choices=KEYS)
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit("Run as owner-approved sudo in the Pi terminal")
    home = Path(pwd.getpwnam("bchbenjamin").pw_dir)
    target = Path("/etc/personal-ai/mcp.env")
    if target.is_symlink() or not target.is_file() or target.stat().st_uid != 0:
        raise SystemExit("Expected the existing root-owned regular MCP environment")
    try:
        token = read_token(home, args.integration, time.time())
        original = target.read_text()
        new = replace_entry(original, KEYS[args.integration][1], token)
        if original == new:
            print("Integration environment already configured; no change.")
            return 0
        backup = target.with_name("mcp.env.backup-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
        with backup.open("x") as f:
            f.write(original)
        os.chmod(backup, 0o600)
        atomic_write(target, new, 0o640, grp.getgrnam("pai-mcp").gr_gid)
        print(f"Prepared {args.integration} environment. Restart only personal-ai-mcp to apply.")
        print(f"Protected environment backup: {backup}")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        # Exception text could include a credential or line from a private file.
        print(f"Optional integration was not configured ({type(exc).__name__}); inspect credential availability locally.")
        return 2

if __name__ == "__main__":
    os.umask(0o077)
    raise SystemExit(main())

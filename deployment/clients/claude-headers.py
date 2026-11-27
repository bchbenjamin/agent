#!/usr/bin/env python3
"""Claude Code headersHelper; stdout is consumed by Claude, not intended for chat."""
import json
import os
import stat
from pathlib import Path

path = Path.home() / ".config/personal-ai/external-brain/claude.token"
if path.is_symlink() or not path.is_file() or stat.S_IMODE(path.stat().st_mode) != 0o600 or path.stat().st_uid != os.getuid():
    raise SystemExit("Expected an owner-only Claude token file")
token = path.read_text().strip()
if not token.startswith("pai_external-brain_"):
    raise SystemExit("Unexpected external-brain token format")
print(json.dumps({"Authorization": "Bearer " + token}))

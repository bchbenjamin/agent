"""Adapter for running computer-use-linux diagnostic and screen queries."""
import os
import subprocess
from typing import Dict, Any

class ComputerUseAdapter:
    """Interfaces with /usr/local/bin/computer-use-linux CLI."""

    def __init__(self, binary_path: str = "/usr/local/bin/computer-use-linux"):
        self.binary_path = binary_path

    def run_doctor(self) -> Dict[str, Any]:
        env = dict(os.environ)
        env["WAYLAND_DISPLAY"] = env.get("WAYLAND_DISPLAY", "wayland-0")
        env["DISPLAY"] = env.get("DISPLAY", ":0")
        env["XDG_RUNTIME_DIR"] = env.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        try:
            res = subprocess.run([self.binary_path, "doctor"], capture_output=True, text=True, env=env, timeout=10)
            return {"output": res.stdout, "returncode": res.returncode}
        except Exception as e:
            return {"error": str(e), "returncode": -1}

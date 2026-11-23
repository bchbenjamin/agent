"""Systemd CLI adapter."""
import subprocess

class SystemdAdapter:
    """Safely interfaces with systemctl for status and lifecycle commands."""

    def is_active(self, service_name: str, user_mode: bool = False) -> str:
        cmd = ["systemctl"]
        if user_mode:
            cmd.append("--user")
        cmd.extend(["is-active", service_name])
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return res.stdout.strip()
        except Exception:
            return "unknown"

    def restart(self, service_name: str, user_mode: bool = False) -> bool:
        cmd = ["systemctl"]
        if user_mode:
            cmd.append("--user")
        cmd.extend(["restart", service_name])
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return res.returncode == 0
        except Exception:
            return False

"""Systemd adapter with restricted helper execution for the Pi user."""

import os
import subprocess


class SystemdAdapter:
    def __init__(self, privileged_helper: str | None = None):
        self.privileged_helper = privileged_helper or os.environ.get(
            "PAI_PRIVILEGED_HELPER", "/usr/local/libexec/pai-privileged"
        )

    def _as_user(self, argv: list[str], timeout: int) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["sudo", "-n", self.privileged_helper, "user-exec", "--", *argv],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    def is_active(self, service_name: str, user_mode: bool = False) -> str:
        try:
            if user_mode:
                res = self._as_user(
                    ["/usr/bin/systemctl", "--user", "is-active", service_name], 8
                )
            else:
                res = subprocess.run(
                    ["/usr/bin/systemctl", "is-active", service_name],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
            return res.stdout.strip() or "inactive"
        except Exception:
            return "unknown"

    def restart(self, service_name: str, user_mode: bool = False) -> bool:
        try:
            if user_mode:
                res = self._as_user(
                    ["/usr/bin/systemctl", "--user", "restart", service_name], 35
                )
            else:
                res = subprocess.run(
                    [
                        "sudo",
                        "-n",
                        self.privileged_helper,
                        "service-restart",
                        service_name,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=35,
                    check=False,
                )
            return res.returncode == 0
        except Exception:
            return False

"""Unprivileged execution engine for managed nodes."""

from __future__ import annotations

import os
import re
import selectors
import shlex
import signal
import subprocess
import time
from typing import Any

from control_plane.authorization.scopes import ScopeValidator


class TaskRunner:
    MAX_TIMEOUT = 120
    MAX_OUTPUT = 32768
    PRIVILEGE_ESCALATORS = {"sudo", "su", "pkexec", "doas", "runuser"}

    def __init__(self):
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            raise RuntimeError("Node Agent must never run as root")
        self.execution_helper = os.environ.get("PAI_EXECUTION_HELPER", "")
        self.require_user_helper = (
            os.environ.get("PAI_NODE_AGENT_REQUIRE_USER_HELPER", "false").lower()
            == "true"
        )

    @staticmethod
    def _decode_output(buffer: bytearray, truncated: bool) -> str:
        text = bytes(buffer).decode("utf-8", errors="replace")
        return text + ("\n...[output truncated]" if truncated else "")

    def _run(self, argv: list[str], timeout: int) -> dict[str, Any]:
        if self.execution_helper:
            command = ["/usr/bin/sudo", "-n", self.execution_helper, "user-exec", "--", *argv]
        elif self.require_user_helper:
            return {
                "error": "Required user execution helper is not configured",
                "returncode": 126,
            }
        else:
            command = argv

        process = None
        selector = selectors.DefaultSelector()
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        truncated = {"stdout": False, "stderr": False}
        timed_out = False
        try:
            process = subprocess.Popen(
                command,
                shell=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                start_new_session=True,
            )
            selector.register(process.stdout, selectors.EVENT_READ, "stdout")
            selector.register(process.stderr, selectors.EVENT_READ, "stderr")
            deadline = time.monotonic() + min(max(int(timeout), 1), self.MAX_TIMEOUT)

            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    break
                for key, _ in selector.select(min(remaining, 0.2)):
                    chunk = os.read(key.fd, 8192)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                        continue
                    name = key.data
                    room = self.MAX_OUTPUT - len(buffers[name])
                    if room > 0:
                        buffers[name].extend(chunk[:room])
                    if len(chunk) > room:
                        truncated[name] = True

            remaining = max(0.01, deadline - time.monotonic())
            if not timed_out:
                try:
                    process.wait(timeout=remaining)
                except subprocess.TimeoutExpired:
                    timed_out = True
            if timed_out:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)
                return {
                    "stdout": self._decode_output(
                        buffers["stdout"], truncated["stdout"]
                    ),
                    "stderr": self._decode_output(
                        buffers["stderr"], truncated["stderr"]
                    ),
                    "error": "Execution timed out",
                    "returncode": 124,
                }
            return {
                "stdout": self._decode_output(buffers["stdout"], truncated["stdout"]),
                "stderr": self._decode_output(buffers["stderr"], truncated["stderr"]),
                "returncode": process.returncode,
            }
        except FileNotFoundError:
            return {"error": f"Executable not found: {command[0]}", "returncode": 127}
        except Exception as exc:
            if process and process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)
            return {"error": f"{type(exc).__name__}: {exc}", "returncode": 1}
        finally:
            selector.close()
            if process:
                for stream in (process.stdout, process.stderr):
                    if stream and not stream.closed:
                        stream.close()

    def run_command(
        self, argv: list[str] | str, timeout: int = 30, approved: bool = False
    ) -> dict[str, Any]:
        if isinstance(argv, str):
            try:
                argv = shlex.split(argv)
            except ValueError as exc:
                return {"error": f"Invalid command syntax: {exc}", "returncode": 2}
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(x, str) for x in argv)
        ):
            return {
                "error": "argv must be a non-empty array of strings",
                "returncode": 2,
            }
        if len(argv) > 128 or sum(map(len, argv)) > 16384:
            return {"error": "Command arguments exceed limits", "returncode": 2}
        if any(
            str(arg).rsplit("/", 1)[-1] in self.PRIVILEGE_ESCALATORS for arg in argv
        ):
            return {
                "error": "Direct privilege escalation is blocked; use an approved Personal AI system operation",
                "returncode": 1,
            }
        if argv[0].rsplit("/", 1)[-1] in {"bash", "sh", "zsh", "dash"} and re.search(
            r"\b(sudo|su|pkexec|doas|runuser)\b", " ".join(argv[1:])
        ):
            return {
                "error": "Direct privilege escalation is blocked; use an approved Personal AI system operation",
                "returncode": 1,
            }
        if (
            ScopeValidator.requires_payload_approval("exec", {"argv": argv})
            and not approved
        ):
            return {
                "error": "Sensitive command rejected without explicit approval",
                "returncode": 1,
            }
        return self._run(argv, timeout)

    def run_shell(
        self, command: str, approved: bool, timeout: int = 30
    ) -> dict[str, Any]:
        if not approved:
            return {
                "error": "Shell execution requires explicit approval",
                "returncode": 126,
            }
        if not isinstance(command, str) or not command.strip() or len(command) > 16384:
            return {"error": "Invalid shell command", "returncode": 2}
        if re.search(r"\b(sudo|su|pkexec|doas|runuser)\b", command):
            return {
                "error": "Direct privilege escalation is blocked; use an approved Personal AI system operation",
                "returncode": 1,
            }
        return self._run(["/bin/bash", "-lc", command], timeout)

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        op = task.get("operation")
        payload = task.get("payload") or {}
        timeout = payload.get("timeout", 30)
        if op == "exec":
            return self.run_command(
                payload.get("argv"), timeout, bool(task.get("approved"))
            )
        if op == "shell":
            return self.run_shell(
                payload.get("command", ""), bool(task.get("approved")), timeout
            )
        if op == "service_status":
            from node_agent.system_management.services import ServiceManager

            name = payload.get("service", "")
            return {
                "service": name,
                "status": ServiceManager().get_status(name),
                "returncode": 0,
            }
        if op == "service_restart":
            from node_agent.system_management.services import ServiceManager

            name = payload.get("service", "")
            ok = ServiceManager().restart_service(name)
            return {"service": name, "restarted": ok, "returncode": 0 if ok else 1}
        return {"error": f"Unsupported operation: {op}", "returncode": 2}

"""Long-running outbound-poll node agent."""

from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path
from typing import Any

import httpx

from node_agent.execution.runner import TaskRunner


class NodeAgent:
    def __init__(
        self,
        node_id: str,
        api_url: str,
        node_token: str = "",
        poll_interval: float = 3.0,
        http_client: httpx.Client | None = None,
    ):
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            raise RuntimeError("Node Agent must never run as root")
        self.node_id = node_id
        self.api_url = api_url.rstrip("/")
        self.node_token = node_token
        self.poll_interval = poll_interval
        trust_env = os.environ.get("PAI_HTTP_TRUST_ENV", "false").lower() == "true"
        self.http = http_client or httpx.Client(timeout=20, trust_env=trust_env)
        self.runner = TaskRunner()
        pending = os.environ.get("PAI_NODE_PENDING_DIR")
        self.pending_dir = Path(pending).expanduser() if pending else None
        if self.pending_dir:
            self.pending_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.chmod(self.pending_dir, 0o700)
        self._running = False

    def _headers(self) -> dict[str, str]:
        if not self.node_token:
            raise RuntimeError("Node token is not configured")
        return {"Authorization": f"Bearer {self.node_token}"}

    @staticmethod
    def _uptime() -> int:
        try:
            return int(float(Path("/proc/uptime").read_text().split()[0]))
        except Exception:
            return 0

    def get_node_status(self) -> dict[str, Any]:
        mem_total = mem_available = 0
        try:
            for line in Path("/proc/meminfo").read_text().splitlines():
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1])
        except Exception:
            pass
        return {
            "node_id": self.node_id,
            "hostname": platform.node(),
            "architecture": platform.machine(),
            "platform": platform.platform(),
            "cpu_count": os.cpu_count() or 1,
            "memory_total_kb": mem_total,
            "memory_available_kb": mem_available,
            "uptime_seconds": self._uptime(),
            "tailscale_ip": os.environ.get("PAI_TAILSCALE_IP") or None,
            "status": "healthy",
        }

    def register(self, enrollment_token: str, tailscale_ip: str | None = None) -> str:
        status = self.get_node_status()
        tailscale_ip = tailscale_ip or os.environ.get("PAI_TAILSCALE_IP") or None
        response = self.http.post(
            f"{self.api_url}/v1/nodes/register",
            headers={"X-Node-Enrollment-Token": enrollment_token},
            json={
                "node_id": self.node_id,
                "hostname": status["hostname"],
                "architecture": status["architecture"],
                "ram_mb": status["memory_total_kb"] // 1024,
                "tier": os.environ.get("PAI_NODE_TIER", "primary_worker"),
                "capabilities": ["terminal", "systemd", "context"],
                "tailscale_ip": tailscale_ip,
                "metadata": status,
            },
        )
        response.raise_for_status()
        self.node_token = response.json()["node_token"]
        return self.node_token

    def _persist_pending_result(
        self, task_id: str, payload: dict[str, Any]
    ) -> Path | None:
        if not self.pending_dir:
            return None
        if not task_id.startswith("task_") or not task_id.replace("_", "").isalnum():
            raise ValueError("Invalid task ID for pending result")
        target = self.pending_dir / f"{task_id}.json"
        temporary = self.pending_dir / f".{task_id}.{os.getpid()}.tmp"
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(
                {"task_id": task_id, "payload": payload}, stream, separators=(",", ":")
            )
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        return target

    def _report_pending_result(
        self, task_id: str, payload: dict[str, Any], path: Path | None
    ) -> bool:
        response = self.http.post(
            f"{self.api_url}/v1/nodes/{self.node_id}/tasks/{task_id}/result",
            headers=self._headers(),
            json=payload,
        )
        if response.status_code == 409:
            if path:
                path.unlink(missing_ok=True)
            return False
        response.raise_for_status()
        if path:
            path.unlink(missing_ok=True)
        return True

    def flush_pending_results(self) -> None:
        if not self.pending_dir or not self.pending_dir.exists():
            return
        for path in sorted(self.pending_dir.glob("task_*.json")):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                self._report_pending_result(record["task_id"], record["payload"], path)
            except (
                OSError,
                ValueError,
                KeyError,
                json.JSONDecodeError,
                httpx.HTTPError,
            ):
                # Keep the durable result and retry after the next API reconnect.
                continue

    def run_once(self) -> bool:
        self.flush_pending_results()
        status = self.get_node_status()
        self.http.post(
            f"{self.api_url}/v1/nodes/{self.node_id}/heartbeat",
            headers=self._headers(),
            json=status,
        ).raise_for_status()
        response = self.http.post(
            f"{self.api_url}/v1/nodes/{self.node_id}/tasks/next",
            headers=self._headers(),
        )
        response.raise_for_status()
        task = response.json().get("task")
        if not task:
            return False
        result = self.runner.execute(task)
        payload: dict[str, Any] = {"result": result}
        if result.get("error"):
            payload["error"] = str(result["error"])[:2048]
        pending_path = self._persist_pending_result(task["task_id"], payload)
        self._report_pending_result(task["task_id"], payload, pending_path)
        return True

    def run_forever(self) -> None:
        self._running = True
        while self._running:
            try:
                self.run_once()
            except (httpx.HTTPError, OSError):
                pass
            time.sleep(self.poll_interval)

    def stop(self) -> None:
        self._running = False
        self.http.close()

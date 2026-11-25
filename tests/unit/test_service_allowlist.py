"""The node agent can inspect the core stack but cannot restart itself."""

import runpy
import subprocess
from pathlib import Path
from unittest.mock import patch

from node_agent.system_management.services import ServiceManager


def test_service_restart_allowlist():
    manager = ServiceManager()
    assert "personal-ai-api.service" in manager.RESTARTABLE_SYSTEM_SERVICES
    assert "personal-ai-mcp.service" in manager.RESTARTABLE_SYSTEM_SERVICES
    assert "personal-ai-node.service" in manager.SYSTEM_SERVICES
    assert "personal-ai-node.service" not in manager.RESTARTABLE_SYSTEM_SERVICES
    assert manager.get_status("unknown.service") == "forbidden"
    assert manager.restart_service("unknown.service") is False


def test_privileged_helper_runs_command_as_regular_user():
    helper = Path(__file__).resolve().parents[2] / "deployment/privileged/pai-privileged"
    user_exec = runpy.run_path(str(helper))["user_exec"]

    with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)) as run:
        assert user_exec(["/usr/bin/id", "-un"]) == 0

    assert run.call_args.args[0] == [
        "/usr/sbin/runuser", "--preserve-environment", "-u", "bchbenjamin",
        "--", "/usr/bin/id", "-un",
    ]
    assert run.call_args.kwargs["stdin"] == subprocess.DEVNULL

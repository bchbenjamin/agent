"""The node agent can inspect the core stack but cannot restart itself."""

from node_agent.system_management.services import ServiceManager


def test_service_restart_allowlist():
    manager = ServiceManager()
    assert "personal-ai-api.service" in manager.RESTARTABLE_SYSTEM_SERVICES
    assert "personal-ai-mcp.service" in manager.RESTARTABLE_SYSTEM_SERVICES
    assert "personal-ai-node.service" in manager.SYSTEM_SERVICES
    assert "personal-ai-node.service" not in manager.RESTARTABLE_SYSTEM_SERVICES
    assert manager.get_status("unknown.service") == "forbidden"
    assert manager.restart_service("unknown.service") is False

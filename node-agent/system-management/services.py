"""Whitelisted system and user service management."""

from node_agent.adapters.systemd import SystemdAdapter


class ServiceManager:
    SYSTEM_SERVICES = {
        "beeper.service",
        "lightdm.service",
        "wayvnc.service",
        "tailscaled.service",
        "personal-ai-node.service",
        "personal-ai-api.service",
        "personal-ai-mcp.service",
    }
    RESTARTABLE_SYSTEM_SERVICES = SYSTEM_SERVICES - {"personal-ai-node.service"}
    USER_SERVICES = {
        "at-spi-dbus-bus.service",
        "hermes-gateway-e86e8d0b.service",
    }
    WHITELISTED_SERVICES = SYSTEM_SERVICES | USER_SERVICES

    def __init__(self):
        self.adapter = SystemdAdapter()

    def get_status(self, service_name: str) -> str:
        if service_name not in self.WHITELISTED_SERVICES:
            return "forbidden"
        return self.adapter.is_active(
            service_name, user_mode=service_name in self.USER_SERVICES
        )

    def restart_service(self, service_name: str) -> bool:
        if service_name not in (self.RESTARTABLE_SYSTEM_SERVICES | self.USER_SERVICES):
            return False
        return self.adapter.restart(
            service_name, user_mode=service_name in self.USER_SERVICES
        )

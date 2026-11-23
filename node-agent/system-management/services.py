"""Service management interface for node agent."""
from typing import Dict, Any
from ..adapters.systemd import SystemdAdapter

class ServiceManager:
    """Manages whitelisted node services via scoped adapter."""

    WHITELISTED_SERVICES = {
        "beeper.service",
        "lightdm.service",
        "wayvnc.service",
        "tailscaled.service",
        "at-spi-dbus-bus.service"
    }

    def __init__(self):
        self.adapter = SystemdAdapter()

    def get_status(self, service_name: str) -> str:
        if service_name not in self.WHITELISTED_SERVICES:
            return "forbidden"
        return self.adapter.is_active(service_name)

    def restart_service(self, service_name: str) -> bool:
        if service_name not in self.WHITELISTED_SERVICES:
            return False
        return self.adapter.restart(service_name)

"""Adapters module."""
from .systemd import SystemdAdapter
from .uinput import UinputAdapter

__all__ = ["SystemdAdapter", "UinputAdapter"]

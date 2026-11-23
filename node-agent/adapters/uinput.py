"""Uinput device permissions adapter."""
import os
import stat

class UinputAdapter:
    """Checks uinput device access for virtual input simulation."""

    DEVICE_PATH = "/dev/uinput"

    @classmethod
    def check_access(cls) -> bool:
        if not os.path.exists(cls.DEVICE_PATH):
            return False
        return os.access(cls.DEVICE_PATH, os.R_OK | os.W_OK)

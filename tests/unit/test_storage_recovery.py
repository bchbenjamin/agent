import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "deployment/recovery/personal-ai-storage-recovery.py"
SPEC = importlib.util.spec_from_file_location("pai_storage_recovery", MODULE_PATH)
recovery = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(recovery)


def result(code=0, stdout=""):
    return subprocess.CompletedProcess([], code, stdout, "")


class TestStorageRecovery(unittest.TestCase):
    def test_unmounted_volume_never_starts_services_or_attempts_mount(self):
        with patch.object(recovery, "_run", return_value=result(1)) as run:
            self.assertEqual(recovery.recover(), 0)
            run.assert_called_once_with("findmnt", "-n", "-o", "UUID", "--target", recovery.MOUNT)

    def test_wrong_volume_is_rejected(self):
        with patch.object(recovery, "_run", return_value=result(stdout="not-the-pi-ssd\n")) as run:
            self.assertEqual(recovery.recover(), 0)
            run.assert_called_once_with("findmnt", "-n", "-o", "UUID", "--target", recovery.MOUNT)

    def test_services_start_only_after_exact_mount_and_api_health(self):
        calls = []

        def fake_run(*args):
            calls.append(args)
            if args[:2] == ("systemctl", "is-active"):
                return result(3)
            return result()

        with patch.object(recovery, "_verified_mount", return_value=True), patch.object(
            recovery, "_run", side_effect=fake_run
        ), patch.object(recovery, "_api_healthy", return_value=True):
            self.assertEqual(recovery.recover(), 0)

        self.assertIn(("systemctl", "start", "personal-ai-api.service"), calls)
        self.assertIn(("systemctl", "start", "personal-ai-mcp.service"), calls)
        self.assertLess(
            calls.index(("systemctl", "start", "personal-ai-api.service")),
            calls.index(("systemctl", "start", "personal-ai-mcp.service")),
        )

    def test_mcp_stays_stopped_when_api_health_fails(self):
        calls = []

        def fake_run(*args):
            calls.append(args)
            return result(3) if args[:2] == ("systemctl", "is-active") else result()

        with patch.object(recovery, "_verified_mount", return_value=True), patch.object(
            recovery, "_run", side_effect=fake_run
        ), patch.object(recovery, "_api_healthy", return_value=False):
            self.assertEqual(recovery.recover(), 1)
        self.assertNotIn(("systemctl", "start", "personal-ai-mcp.service"), calls)


if __name__ == "__main__":
    unittest.main()

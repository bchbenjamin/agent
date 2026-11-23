"""Unprivileged task execution runner."""
import subprocess
from typing import Dict, Any

class TaskRunner:
    """Executes validated commands within an unprivileged sandbox."""

    def run_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        if not command:
            return {"error": "Empty command", "returncode": -1}

        # Forbid dangerous destructive root commands from unprivileged runner
        forbidden = ["rm -rf /", "mkfs", "wipefs", "dd if="]
        if any(f in command for f in forbidden):
            return {"error": "Dangerous command rejected by execution policy", "returncode": 1}

        try:
            res = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "stdout": res.stdout,
                "stderr": res.stderr,
                "returncode": res.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Execution timed out", "returncode": 124}
        except Exception as e:
            return {"error": str(e), "returncode": -1}

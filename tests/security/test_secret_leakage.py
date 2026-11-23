"""Automated secret-scanning test ensuring no private tokens exist in the repository."""
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

SUSPICIOUS_PATTERNS = [
    (re.compile(r"AI_GATEWAY_API_KEY\s*=\s*['\"]?[a-zA-Z0-9_\-]{20,}['\"]?"), "Exposed AI Gateway key"),
    (re.compile(r"API_SERVER_KEY\s*=\s*['\"]?[a-f0-9]{64}['\"]?"), "Exposed 64-hex API server key"),
    (re.compile(r"cb_[a-zA-Z0-9_\-]{20,}"), "Exposed Simular Box key"),
    (re.compile(r"BEGIN (RSA|OPENSSH|EC|PRIVATE) KEY"), "Private key block"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub Personal Access Token"),
]

FORBIDDEN_EXTENSIONS = [
    ".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm",
    ".keyring", ".enc", ".bak"
]

class TestSecretLeakage(unittest.TestCase):

    def test_no_forbidden_files_or_secrets(self):
        violations = []

        for root, dirs, files in os.walk(REPO_ROOT):
            # Skip .git directory
            if "/.git" in root or root.endswith("/.git"):
                continue

            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, REPO_ROOT)

                # Check extensions
                _, ext = os.path.splitext(file)
                if ext in FORBIDDEN_EXTENSIONS:
                    violations.append(f"Forbidden binary/secret file committed: {rel_path}")

                # Check secret patterns in text files
                if ext in [".py", ".sh", ".yaml", ".yml", ".json", ".md", ".txt", ".template"]:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            for pattern, desc in SUSPICIOUS_PATTERNS:
                                # Ignore template replacement strings
                                if "replace-" in content or "replace_with" in content or "<your" in content:
                                    continue
                                if pattern.search(content):
                                    violations.append(f"{desc} found in {rel_path}")
                    except Exception as e:
                        violations.append(f"Could not read {rel_path}: {e}")

        self.assertEqual(len(violations), 0, f"Secret leakage detected:\n" + "\n".join(violations))

if __name__ == "__main__":
    unittest.main()

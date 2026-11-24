"""Node agent enrollment and runtime CLI."""

import argparse
import json
import os
import stat
from pathlib import Path

from node_agent.core.agent import NodeAgent


def _save_token(path: str, token: str) -> None:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(
        target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR
    )
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(token + "\n")
    os.chmod(target, 0o600)


def main():
    parser = argparse.ArgumentParser(prog="pai-node-agent")
    parser.add_argument("--node-id", default=os.environ.get("PAI_NODE_ID", "pi5"))
    parser.add_argument(
        "--api-url",
        default=os.environ.get("PAI_API_URL", "https://api.hermes.bchbenjamin.in"),
    )
    parser.add_argument(
        "--token-file",
        default=os.environ.get(
            "PAI_NODE_TOKEN_FILE", "~/.config/personal-ai/node-token"
        ),
    )
    parser.add_argument("--enroll", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error("Refusing to run as root")
    agent = NodeAgent(args.node_id, args.api_url, "")
    token_path = Path(args.token_file).expanduser()
    if args.enroll:
        enrollment = os.environ.get("PAI_NODE_ENROLLMENT_TOKEN")
        if not enrollment:
            parser.error("PAI_NODE_ENROLLMENT_TOKEN is required for enrollment")
        token = agent.register(enrollment)
        _save_token(str(token_path), token)
        print(f"Node enrolled. Credential stored at {token_path} (mode 0600).")
        return
    if not token_path.exists():
        parser.error(f"Node token file missing: {token_path}; enroll first")
    if stat.S_IMODE(token_path.stat().st_mode) & 0o077:
        parser.error("Node token file must have permissions 0600")
    agent.node_token = token_path.read_text(encoding="utf-8").strip()
    if args.once:
        print(
            json.dumps(
                {"task_processed": agent.run_once(), "status": agent.get_node_status()},
                indent=2,
            )
        )
    else:
        agent.run_forever()


if __name__ == "__main__":
    main()

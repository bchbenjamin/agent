"""Administrative and context-indexing CLI for Personal AI."""

import argparse
import json
import os
import stat
from pathlib import Path

import httpx

from control_plane.authentication.tokens import TokenManager
from control_plane.authorization.scopes import ALL_SCOPES
from control_plane.storage import get_store

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".csv",
    ".log",
}
SKIP_PARTS = {
    ".git",
    ".ssh",
    ".aws",
    ".config",
    ".local",
    ".cache",
    ".hermes-pi",
    ".beeper",
    ".gnupg",
    ".pki",
    ".password-store",
    ".kube",
    ".docker",
    ".npm",
    ".claude",
    ".codex",
    ".thunderbird",
    ".mozilla",
    ".var",
    "node_modules",
    "mcp-tokens",
    "keyrings",
    "Beeper",
}
SKIP_NAMES = {
    ".env",
    "credentials",
    "id_rsa",
    "id_ed25519",
    "auth.json",
    "oauth_creds.json",
}
SKIP_NAME_PARTS = (
    "secret",
    "password",
    "token",
    "credential",
    "private-key",
    "keyring",
)


def _context_token() -> str:
    token_path = Path(
        os.environ.get(
            "PAI_CONTEXT_INDEX_TOKEN_FILE",
            "~/.config/personal-ai/context-index-token",
        )
    ).expanduser()
    if not token_path.is_file():
        raise SystemExit(f"Context-index token file missing: {token_path}")
    if stat.S_IMODE(token_path.stat().st_mode) & 0o077:
        raise SystemExit("Context-index token file must have permissions 0600")
    token = token_path.read_text(encoding="utf-8").strip()
    if not token:
        raise SystemExit("Context-index token file is empty")
    return token


def _index_document(title: str, body: str, source: str) -> str:
    if len(body.encode("utf-8")) > 1_000_000:
        raise SystemExit("Context document exceeds 1 MiB")
    token = _context_token()
    api_url = os.environ.get("PAI_API_URL", "https://api.hermes.bchbenjamin.in").rstrip(
        "/"
    )
    trust_env = os.environ.get("PAI_HTTP_TRUST_ENV", "false").lower() == "true"
    with httpx.Client(timeout=30, trust_env=trust_env) as client:
        response = client.post(
            f"{api_url}/v1/context/index",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": title, "body": body, "source": source},
        )
        response.raise_for_status()
        return response.json()["document_id"]


def _index_path(target: str) -> dict[str, int]:
    roots = [
        Path(x).expanduser().resolve()
        for x in os.environ.get("PAI_CONTEXT_INDEX_ROOTS", "").split(",")
        if x.strip()
    ]
    if not roots:
        raise SystemExit(
            "Set PAI_CONTEXT_INDEX_ROOTS to approved roots before indexing."
        )
    requested = Path(target).expanduser()
    if requested.is_symlink():
        raise SystemExit(f"Refusing to index a symlink target: {requested}")
    path = requested.resolve()
    if not any(path == root or root in path.parents for root in roots):
        raise SystemExit(f"Refusing to index outside configured roots: {path}")
    candidates = (
        [requested]
        if path.is_file()
        else sorted(p for p in path.rglob("*") if p.is_file())
    )
    indexed = skipped = failed = 0
    for candidate in candidates:
        # Check the unresolved path first: resolve() erases the symlink bit.
        if candidate.is_symlink():
            skipped += 1
            continue
        try:
            file = candidate.resolve(strict=True)
            if not any(file == root or root in file.parents for root in roots):
                skipped += 1
                continue
            if (
                any(part in SKIP_PARTS for part in candidate.parts)
                or any(part in SKIP_PARTS for part in file.parts)
                or file.name in SKIP_NAMES
                or any(x in file.name.lower() for x in SKIP_NAME_PARTS)
                or file.suffix.lower() not in TEXT_EXTENSIONS
            ):
                skipped += 1
                continue
            if file.stat().st_size > 1_000_000:
                skipped += 1
                continue
            body = file.read_text(encoding="utf-8")
            _index_document(file.name, body, str(file))
            indexed += 1
        except (OSError, UnicodeError, httpx.HTTPError):
            failed += 1
    return {"indexed": indexed, "skipped": skipped, "failed": failed}


def main():
    parser = argparse.ArgumentParser(prog="pai-admin")
    sub = parser.add_subparsers(dest="command", required=True)
    issue = sub.add_parser("issue-token")
    issue.add_argument("--client-id", required=True)
    issue.add_argument("--client-type", default="mcp")
    issue.add_argument("--user", default="owner")
    issue.add_argument(
        "--scopes", default="context:read,nodes:read,files:read,terminal:execute"
    )
    revoke = sub.add_parser("revoke-token")
    revoke.add_argument("--token", required=True)
    revoke_client = sub.add_parser("revoke-client")
    revoke_client.add_argument("--client-id", required=True)
    doc = sub.add_parser("index-document")
    doc.add_argument("--title", required=True)
    doc.add_argument("--source", default="manual")
    doc.add_argument("--file", required=True)
    index = sub.add_parser("index-path")
    index.add_argument("--path", required=True)
    sub.add_parser("verify-audit")
    args = parser.parse_args()

    if args.command == "issue-token":
        store = get_store()
        scopes = set(filter(None, args.scopes.split(",")))
        unknown = scopes - ALL_SCOPES
        if unknown:
            parser.error("Unknown scopes: " + ", ".join(sorted(unknown)))
        token = TokenManager(store).issue_token(
            args.client_id, args.client_type, args.user, scopes
        )
        print(token)
    elif args.command == "revoke-token":
        print("revoked" if get_store().revoke_token(args.token) else "not found")
    elif args.command == "revoke-client":
        print("revoked" if get_store().revoke_client(args.client_id) else "not found")
    elif args.command == "index-document":
        with open(args.file, encoding="utf-8") as f:
            body = f.read()
        print(_index_document(args.title, body, args.source))
    elif args.command == "index-path":
        print(json.dumps(_index_path(args.path)))
    elif args.command == "verify-audit":
        store = get_store()
        valid = store.verify_audit_chain()
        print(json.dumps({"valid": valid, "recent": store.recent_audit(10)}, indent=2))
        raise SystemExit(0 if valid else 1)


if __name__ == "__main__":
    main()

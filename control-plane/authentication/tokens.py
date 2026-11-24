"""Persistent bearer-token manager. Only SHA-256 token hashes are stored."""

from typing import Any

from control_plane.storage import SQLiteStore, get_store


class TokenManager:
    def __init__(self, store: SQLiteStore | None = None):
        self.store = store or get_store()

    def issue_token(
        self, client_id: str, client_type: str, user: str, scopes: set[str]
    ) -> str:
        return self.store.issue_token(client_id, client_type, user, scopes)

    def verify_token(self, token: str) -> dict[str, Any] | None:
        return self.store.verify_token(token)

    def revoke_token(self, token: str) -> bool:
        return self.store.revoke_token(token)

    def revoke_client(self, client_id: str) -> bool:
        return self.store.revoke_client(client_id)

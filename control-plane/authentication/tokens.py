"""Authentication and token verification for Personal AI Infrastructure."""
import secrets
import hashlib
from typing import Dict, Optional, Set

class TokenManager:
    """Manages scoped bearer tokens and mutual node authentication."""

    def __init__(self):
        # Maps token_hash -> metadata {client_id, user, scopes, client_type}
        self._tokens: Dict[str, Dict] = {}

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def issue_token(self, client_id: str, client_type: str, user: str, scopes: Set[str]) -> str:
        raw_token = f"pai_{client_type}_{secrets.token_urlsafe(32)}"
        token_hash = self.hash_token(raw_token)
        self._tokens[token_hash] = {
            "client_id": client_id,
            "client_type": client_type,
            "user": user,
            "scopes": set(scopes),
            "active": True
        }
        return raw_token

    def verify_token(self, token: str) -> Optional[Dict]:
        token_hash = self.hash_token(token)
        meta = self._tokens.get(token_hash)
        if meta and meta.get("active"):
            return meta
        return None

    def revoke_token(self, token: str) -> bool:
        token_hash = self.hash_token(token)
        if token_hash in self._tokens:
            self._tokens[token_hash]["active"] = False
            return True
        return False

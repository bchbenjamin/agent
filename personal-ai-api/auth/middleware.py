"""Authentication middleware for Personal AI API."""
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Callable, Set

# Mock/singleton token manager instance for the API server
from ...control_plane.authentication.tokens import TokenManager
from ...control_plane.authorization.scopes import ScopeValidator

token_manager = TokenManager()
security = HTTPBearer()

def get_current_client(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    token = credentials.credentials
    meta = token_manager.verify_token(token)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return meta

def require_scope(required_scope: str) -> Callable:
    def scope_checker(client: dict = Security(get_current_client)) -> dict:
        scopes: Set[str] = client.get("scopes", set())
        if not ScopeValidator.has_scope(scopes, required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires permission scope: {required_scope}",
            )
        return client
    return scope_checker

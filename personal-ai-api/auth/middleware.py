"""Authentication dependencies for Personal AI API."""

from typing import Callable, Set

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from control_plane.authentication.tokens import TokenManager
from control_plane.authorization.scopes import ScopeValidator

token_manager = TokenManager()
security = HTTPBearer(auto_error=False)


def get_current_client(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    meta = token_manager.verify_token(credentials.credentials)
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

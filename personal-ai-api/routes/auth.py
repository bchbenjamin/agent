"""Client identity introspection endpoint for authenticated adapters."""

from fastapi import APIRouter, Depends

from ..auth.middleware import get_current_client

router = APIRouter()


@router.get("/auth/me")
def whoami(client: dict = Depends(get_current_client)):
    return {
        "client_id": client["client_id"],
        "client_type": client["client_type"],
        "user": client["user"],
        "scopes": sorted(client["scopes"]),
    }

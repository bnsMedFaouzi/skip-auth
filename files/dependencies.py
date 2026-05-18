from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .models import AuthContext
from .service import AuthService
from .settings import settings as _settings

_bearer = HTTPBearer(auto_error=False)


def get_auth_service() -> AuthService:
    """Override in tests to inject a mock."""
    return AuthService(_settings)


async def get_auth_context(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
    service: Annotated[AuthService, Depends(get_auth_service)] = None,
) -> AuthContext:
    forwarded_host = request.headers.get("x-forwarded-host")

    if service.is_trusted_host(forwarded_host):
        return service.authenticate_internal(forwarded_host)

    return service.authenticate_bearer(credentials)


# ─── Reusable type aliases ────────────────────────────────────────────────────

RequireAuth = Annotated[AuthContext, Depends(get_auth_context)]

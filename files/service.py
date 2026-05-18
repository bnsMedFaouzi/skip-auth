from fastapi.security import HTTPAuthorizationCredentials

from .exceptions import InvalidTokenError, MissingTokenError
from .models import AuthContext, AuthMethod
from .settings import Settings


class AuthService:
    """Stateless auth service — inject via Depends for testability."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def authenticate_internal(self, forwarded_host: str) -> AuthContext:
        return AuthContext(
            user="internal",
            method=AuthMethod.TRUSTED_HOST,
            forwarded_host=forwarded_host,
        )

    def authenticate_bearer(
        self, credentials: HTTPAuthorizationCredentials | None
    ) -> AuthContext:
        if credentials is None:
            raise MissingTokenError()
        if not self._verify_token(credentials.credentials):
            raise InvalidTokenError()
        return AuthContext(user="authenticated", method=AuthMethod.BEARER)

    def is_trusted_host(self, host: str | None) -> bool:
        return bool(host and host in self._settings.trusted_forwarded_hosts)

    def _verify_token(self, token: str) -> bool:
        # Remplace par une vérification JWT, DB, etc.
        import hmac
        return hmac.compare_digest(token, self._settings.secret_token)

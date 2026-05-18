import pytest
from fastapi.testclient import TestClient

from auth import AuthContext, AuthMethod, AuthService, get_auth_service
from auth.settings import Settings
from main import app


# ─── AuthService unit tests ───────────────────────────────────────────────────

@pytest.fixture
def service() -> AuthService:
    return AuthService(Settings(secret_token="test-token", trusted_forwarded_hosts=frozenset({"trusted.host"})))


def test_trusted_host_recognized(service: AuthService):
    assert service.is_trusted_host("trusted.host") is True


def test_unknown_host_rejected(service: AuthService):
    assert service.is_trusted_host("evil.com") is False


def test_none_host_rejected(service: AuthService):
    assert service.is_trusted_host(None) is False


def test_internal_auth_context(service: AuthService):
    ctx = service.authenticate_internal("trusted.host")
    assert ctx.method == AuthMethod.TRUSTED_HOST
    assert ctx.is_internal is True


# ─── Integration tests ────────────────────────────────────────────────────────

def _override_service(token: str = "test-token", hosts: frozenset = frozenset({"trusted.host"})):
    def _factory():
        return AuthService(Settings(secret_token=token, trusted_forwarded_hosts=hosts))
    return _factory


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_auth_service] = _override_service()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_trusted_host_bypasses_auth(client: TestClient):
    r = client.get("/protected", headers={"x-forwarded-host": "trusted.host"})
    assert r.status_code == 200
    assert r.json()["is_internal"] is True


def test_valid_bearer_grants_access(client: TestClient):
    r = client.get("/protected", headers={"Authorization": "Bearer test-token"})
    assert r.status_code == 200


def test_missing_token_returns_401(client: TestClient):
    r = client.get("/protected")
    assert r.status_code == 401


def test_invalid_token_returns_403(client: TestClient):
    r = client.get("/protected", headers={"Authorization": "Bearer wrong"})
    assert r.status_code == 403


def test_untrusted_host_without_token_returns_401(client: TestClient):
    r = client.get("/protected", headers={"x-forwarded-host": "evil.com"})
    assert r.status_code == 401

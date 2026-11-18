import asyncio

import pytest

from backend.pa_api import auth, context


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


def _run_dependency(**kwargs):
    async def collect():
        values = []
        async for ctx in auth.get_context(**kwargs):
            values.append((ctx, context.current()))
        return values

    return asyncio.run(collect())


@pytest.fixture(autouse=True)
def clear_auth_cache():
    auth._USER_CACHE.clear()
    yield
    auth._USER_CACHE.clear()


def test_valid_token_builds_user_context_and_loads_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://supabase.example")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-test-key")
    calls = []

    def fake_get(url, headers, timeout):
        calls.append((url, headers, timeout))
        return FakeResponse(200, {"id": "user-123", "email": "fake@example.test"})

    monkeypatch.setattr(auth.httpx, "get", fake_get)
    monkeypatch.setattr(auth.supabase_auth, "load_user_gemini_key", lambda key, email: "AIza-user")

    values = _run_dependency(authorization="Bearer token-123", x_pa_sandbox=None)

    ctx, active = values[0]
    assert ctx == context.RequestContext("user-123", "fake@example.test", "AIza-user", False)
    assert active == ctx
    assert calls[0][0] == "https://supabase.example/auth/v1/user"
    assert calls[0][1]["Authorization"] == "Bearer token-123"
    assert calls[0][2] == 10.0


def test_token_validation_is_cached_for_sixty_seconds(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://supabase.example")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-test-key")
    calls = []
    monkeypatch.setattr(auth.httpx, "get", lambda *args, **kwargs: calls.append(1) or FakeResponse(200, {"id": "u1"}))
    monkeypatch.setattr(auth.supabase_auth, "load_user_gemini_key", lambda key, email: "")

    _run_dependency(authorization="Bearer cached-token", x_pa_sandbox=None)
    _run_dependency(authorization="Bearer cached-token", x_pa_sandbox=None)

    assert len(calls) == 1


def test_invalid_token_is_401(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://supabase.example")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-test-key")
    monkeypatch.setattr(auth.httpx, "get", lambda *args, **kwargs: FakeResponse(401, {"error": "invalid"}))

    with pytest.raises(auth.ApiError) as exc:
        _run_dependency(authorization="Bearer bad-token", x_pa_sandbox=None)
    assert exc.value.status == 401


def test_sandbox_header_uses_sandbox_context():
    values = _run_dependency(authorization=None, x_pa_sandbox="1")
    assert values[0][0] is context.SANDBOX
    assert values[0][1] is context.SANDBOX


def test_missing_credentials_is_401():
    with pytest.raises(auth.ApiError) as exc:
        _run_dependency(authorization=None, x_pa_sandbox=None)
    assert exc.value.status == 401

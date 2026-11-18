from fastapi.testclient import TestClient

from backend.pa_api import context
from backend.pa_api.main import app
from backend.pa_api.routers import account


client = TestClient(app)


def test_me_signed_in_never_returns_gemini_key(monkeypatch):
    ctx = context.RequestContext("fake-user", "fake@example.test", "AIza-secret-test", False)
    monkeypatch.setattr(account.supabase_auth, "ensure_user_profile", lambda *args, **kwargs: {"display_name": "Fake User", "role": "Processor", "terms_accepted_at": ""})
    monkeypatch.setattr(account.tiers, "check_scan_quota", lambda *args: {"tier": "free", "tier_name": "Beta - Free", "limit": 20, "used": 0, "remaining": 20})
    app.dependency_overrides[account.get_context] = lambda: ctx
    try:
        response = client.get("/api/me")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["ai"]["has_key"] is True
    assert "AIza-secret-test" not in response.text
    assert "gemini_key" not in response.text


def test_me_sandbox_response(monkeypatch):
    app.dependency_overrides[account.get_context] = lambda: context.SANDBOX
    try:
        response = client.get("/api/me")
    finally:
        app.dependency_overrides.clear()
    body = response.json()
    assert response.status_code == 200
    assert body["sandbox"] is True
    assert body["usage"] is None
    assert body["ai"]["has_key"] is False

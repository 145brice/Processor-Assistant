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


def test_accept_terms_sandbox_is_forbidden():
    app.dependency_overrides[account.get_context] = lambda: context.SANDBOX
    try:
        response = client.post("/api/me/accept-terms")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403


def test_accept_terms_success(monkeypatch):
    ctx = context.RequestContext("fake-user", "fake@example.test", "", False)
    monkeypatch.setattr(account.supabase_auth, "accept_terms", lambda *args, **kwargs: {"terms_accepted_at": "now"})
    app.dependency_overrides[account.get_context] = lambda: ctx
    try:
        response = client.post("/api/me/accept-terms")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_accept_terms_save_failure_is_503(monkeypatch):
    ctx = context.RequestContext("fake-user", "fake@example.test", "", False)
    monkeypatch.setattr(account.supabase_auth, "accept_terms", lambda *args, **kwargs: {"_save_error": "offline"})
    app.dependency_overrides[account.get_context] = lambda: ctx
    try:
        response = client.post("/api/me/accept-terms")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "save_failed"


def test_me_reports_accepted_terms(monkeypatch):
    ctx = context.RequestContext("fake-user", "fake@example.test", "", False)
    monkeypatch.setattr(account.supabase_auth, "ensure_user_profile", lambda *args, **kwargs: {"terms_accepted_at": "now"})
    monkeypatch.setattr(account.tiers, "check_scan_quota", lambda *args: {"tier": "free", "tier_name": "Free", "limit": 20, "used": 0, "remaining": 20})
    app.dependency_overrides[account.get_context] = lambda: ctx
    try:
        response = client.get("/api/me")
    finally:
        app.dependency_overrides.clear()
    assert response.json()["terms_accepted"] is True

from fastapi.testclient import TestClient

from backend.pa_api import context
from backend.pa_api.main import app
from backend.pa_api.routers import account


client = TestClient(app)


def with_context(ctx):
    app.dependency_overrides[account.get_context] = lambda: ctx


def test_get_ai_key_never_returns_key(monkeypatch):
    with_context(context.RequestContext("fake-user", "fake@example.test", "AIza-secret-test", False))
    monkeypatch.setattr(account.supabase_auth, "load_user_gemini_key", lambda *args: "AIza-secret-test")
    try:
        response = client.get("/api/ai-key")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["has_key"] is True
    assert "AIza-secret-test" not in response.text


def test_put_tests_before_saving_and_saves_success(monkeypatch):
    calls = []
    with_context(context.RequestContext("fake-user", "fake@example.test", "", False))
    monkeypatch.setattr(account.cloud_client, "ping", lambda *args: (calls.append(args) or (True, "Connected")))
    monkeypatch.setattr(account.supabase_auth, "save_user_gemini_key", lambda *args: {"ok": True})
    try:
        response = client.put("/api/ai-key", json={"key": "AIza-fake"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert calls == [("gemini", "AIza-fake")]
    assert response.json()["has_key"] is True


def test_put_does_not_save_failed_key(monkeypatch):
    with_context(context.RequestContext("fake-user", "fake@example.test", "", False))
    monkeypatch.setattr(account.cloud_client, "ping", lambda *args: (False, "That key is invalid."))
    saved = []
    monkeypatch.setattr(account.supabase_auth, "save_user_gemini_key", lambda *args: saved.append(args) or {"ok": True})
    try:
        response = client.put("/api/ai-key", json={"key": "AIza-fake"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 400
    assert "That key is invalid." in response.text
    assert saved == []


def test_sandbox_cannot_save_or_delete_key():
    with_context(context.SANDBOX)
    try:
        put_response = client.put("/api/ai-key", json={"key": "AIza-fake"})
        delete_response = client.delete("/api/ai-key")
    finally:
        app.dependency_overrides.clear()
    assert put_response.status_code == 403
    assert delete_response.status_code == 403

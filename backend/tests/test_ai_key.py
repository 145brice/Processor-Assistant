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
    monkeypatch.setattr(account.cloud_client, "check_gemini_key", lambda key: (calls.append(key) or (True, "Connected")))
    monkeypatch.setattr(account.supabase_auth, "save_user_gemini_key", lambda *args: {"ok": True})
    try:
        response = client.put("/api/ai-key", json={"key": "AIza-fake"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert calls == ["AIza-fake"]
    assert response.json()["has_key"] is True


def test_put_does_not_save_failed_key(monkeypatch):
    with_context(context.RequestContext("fake-user", "fake@example.test", "", False))
    monkeypatch.setattr(account.cloud_client, "check_gemini_key", lambda key: (False, "That key is invalid."))
    saved = []
    monkeypatch.setattr(account.supabase_auth, "save_user_gemini_key", lambda *args: saved.append(args) or {"ok": True})
    try:
        response = client.put("/api/ai-key", json={"key": "AIza-fake"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 400
    assert "That key is invalid." in response.text
    assert saved == []


def test_empty_key_is_rejected_without_check_or_save(monkeypatch):
    with_context(context.RequestContext("fake-user", "fake@example.test", "", False))
    monkeypatch.setattr(account.cloud_client, "check_gemini_key", lambda key: (_ for _ in ()).throw(AssertionError("checked")))
    saved = []
    monkeypatch.setattr(account.supabase_auth, "save_user_gemini_key", lambda *args: saved.append(args) or {"ok": True})
    try:
        response = client.put("/api/ai-key", json={"key": "  "})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 400
    assert "Paste your Gemini key first." in response.text
    assert saved == []


def test_saved_key_is_checked_once(monkeypatch):
    with_context(context.RequestContext("fake-user", "fake@example.test", "", False))
    calls = []
    monkeypatch.setattr(account.supabase_auth, "load_user_gemini_key", lambda *args: "AIza-saved")
    monkeypatch.setattr(account.cloud_client, "check_gemini_key", lambda key: (calls.append(key) or (True, "Connected")))
    try:
        response = client.post("/api/ai-key/test")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert calls == ["AIza-saved"]


def test_checker_failure_messages_are_returned(monkeypatch):
    messages = [
        "That doesn't look like a Gemini key.",
        "This key isn't allowed to use Gemini yet.",
        "This key has no paid usage available.",
        "Google is getting too many requests right now.",
        "Couldn't reach Google.",
    ]
    for message in messages:
        with_context(context.RequestContext("fake-user", "fake@example.test", "", False))
        monkeypatch.setattr(account.cloud_client, "check_gemini_key", lambda key, message=message: (False, message))
        try:
            response = client.put("/api/ai-key", json={"key": "AIza-fake"})
        finally:
            app.dependency_overrides.clear()
        assert response.status_code == 400
        assert message in response.text


def test_sandbox_cannot_save_or_delete_key():
    with_context(context.SANDBOX)
    try:
        put_response = client.put("/api/ai-key", json={"key": "AIza-fake"})
        delete_response = client.delete("/api/ai-key")
    finally:
        app.dependency_overrides.clear()
    assert put_response.status_code == 403
    assert delete_response.status_code == 403

from fastapi.testclient import TestClient

from backend.pa_api import context
from backend.pa_api.main import app
from backend.pa_api.routers import account, scanning

client = TestClient(app)


def test_saved_scans_are_converted_sorted_and_scoped(monkeypatch):
    ctx = context.RequestContext("user-a", "a@example.test", "", False)
    raw = {"file": "old.pdf", "type": "Approval Letter", "result": {"success": True, "conditions": [], "contacts": {}}, "loan_match": {}}
    monkeypatch.setattr(scanning.scan_history_store, "load", lambda key: {"ok": True, "items": [
        {"id": "old", "ts": 10, "user_key": "user-a", "batch": raw},
        {"id": "new", "ts": 20, "user_key": "user-a", "batch": raw},
        {"id": "other", "ts": 30, "user_key": "other", "batch": raw},
    ]})
    app.dependency_overrides[scanning.get_context] = lambda: ctx
    try:
        response = client.get("/api/scans")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == ["new", "old"]
    assert response.json()["items"][0]["saved_at"].startswith("1970-01-01T00:00:20")


def test_sandbox_scans_are_empty_and_cannot_delete():
    app.dependency_overrides[scanning.get_context] = lambda: context.SANDBOX
    try:
        assert client.get("/api/scans").json() == {"items": []}
        assert client.delete("/api/scans/nope").status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_delete_unknown_scan_is_404(monkeypatch):
    ctx = context.RequestContext("user-a", "a@example.test", "", False)
    monkeypatch.setattr(scanning.scan_history_store, "load", lambda key: {"ok": True, "items": []})
    app.dependency_overrides[scanning.get_context] = lambda: ctx
    try:
        assert client.delete("/api/scans/nope").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_usage_and_pricing_work_in_sandbox(monkeypatch):
    app.dependency_overrides[account.get_context] = lambda: context.SANDBOX
    try:
        assert client.get("/api/usage").status_code == 200
        assert len(client.get("/api/pricing").json()["tiers"]) == 4
    finally:
        app.dependency_overrides.clear()

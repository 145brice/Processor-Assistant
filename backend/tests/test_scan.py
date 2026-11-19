"""POST /api/scan behaviour (task T-21). Offline: Supabase, billing and the loan store are faked."""
import pytest
from fastapi.testclient import TestClient

from backend.pa_api import auth, context, scan_service
from backend.pa_api.errors import ApiError
from backend.pa_api.main import app
from backend.pa_api.normalize import normalize_scanned_conditions, to_contract_conditions
from backend.tests.fake_pdf import BLANK, FAKE_APPROVAL

client = TestClient(app)
SANDBOX = {"X-PA-Sandbox": "1"}
USER = context.RequestContext(user_key="user-test-9", email="fake9@example.test", gemini_key="", sandbox=False)


@pytest.fixture
def offline(monkeypatch):
    saved, logged = [], []
    monkeypatch.setattr(scan_service, "visible_loans", lambda ctx: [])
    monkeypatch.setattr(scan_service.billing, "log_scan", lambda uid, t: logged.append((uid, t)) or {})
    monkeypatch.setattr(scan_service.scan_history_store, "load", lambda uid: {"ok": True, "items": []})
    monkeypatch.setattr(scan_service.scan_history_store, "save", lambda uid, items, email="": saved.append((uid, items)) or {"ok": True})
    monkeypatch.setattr(scan_service.supabase_auth, "ensure_user_profile", lambda *a, **k: {})
    monkeypatch.setattr(scan_service.supabase_auth, "load_private_approval_intelligence", lambda *a, **k: {})
    monkeypatch.setattr(scan_service.supabase_auth, "save_private_approval_intelligence", lambda *a, **k: {"ok": True})
    return {"saved": saved, "logged": logged}


@pytest.fixture
def signed_in():
    async def fake_context():
        with context.use(USER):
            yield USER
    app.dependency_overrides[auth.get_context] = fake_context
    yield
    app.dependency_overrides.pop(auth.get_context, None)


def _scan(doc_type="Approval Letter", pdf=FAKE_APPROVAL, headers=None):
    return client.post("/api/scan", headers=headers or {}, data={"doc_type": doc_type},
                       files={"file": ("doc-test.pdf", pdf, "application/pdf")})


def test_sandbox_scan_returns_normalised_conditions(offline):
    response = _scan(headers=SANDBOX)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["file"] == "doc-test.pdf" and body["type"] == "Approval Letter"
    result = body["result"]
    assert result["success"] is True and result["error"] == ""
    assert result["conditions"], "the fake approval has conditions"
    assert [c["num"] for c in result["conditions"]] == list(range(1, len(result["conditions"]) + 1))
    assert all(c["status"] in {"Needed", "Requested", "Important", "Ready to Clear", "Cleared"} for c in result["conditions"])
    assert body["usage"] is None  # sandbox has no quota
    assert offline["saved"] == [] and offline["logged"] == []  # sandbox never saves or bills


def test_signed_in_scan_is_billed_and_saved_without_raw_text(offline, signed_in, monkeypatch):
    monkeypatch.setattr(scan_service.tiers, "check_scan_quota",
                        lambda uid, p: {"tier": "free", "tier_name": "Free", "limit": 10, "used": 3, "remaining": 7, "next_tier_name": "Starter"})
    response = _scan()
    assert response.status_code == 200, response.text
    assert offline["logged"] == [(USER.user_key, "Approval Letter")]
    ((uid, items),) = offline["saved"]
    assert uid == USER.user_key and items[0]["user_key"] == USER.user_key
    assert "raw_text" not in str(items[0])
    assert response.json()["usage"]["remaining"] == 7


def test_quota_used_up_is_402(offline, signed_in, monkeypatch):
    monkeypatch.setattr(scan_service.tiers, "check_scan_quota",
                        lambda uid, p: {"tier": "free", "tier_name": "Free", "limit": 5, "used": 5, "remaining": 0, "next_tier_name": "Starter"})
    response = _scan()
    assert response.status_code == 402
    assert "Starter" in response.json()["error"]["message"]
    assert offline["logged"] == []


def test_owner_skips_quota(offline, monkeypatch):
    monkeypatch.setenv("PA_OWNER_ADMIN_EMAILS", "owner@example.test")
    owner = context.RequestContext(user_key="owner-1", email="Owner@Example.test", gemini_key="", sandbox=False)
    monkeypatch.setattr(scan_service.tiers, "check_scan_quota", lambda *a: pytest.fail("owner should skip quota"))
    assert scan_service.check_quota(owner) == (None, {})


def test_unknown_type_is_400(offline):
    response = _scan(doc_type="Unknown", headers=SANDBOX)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "choose_doc_type"


def test_unreadable_approval_fails_cleanly(offline):
    response = _scan(pdf=BLANK, headers=SANDBOX)
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["success"] is False and result["error"]
    assert result["conditions"] == []


def test_normaliser_reads_pipe_tables_and_routes_parties():
    raw = (
        "| # | Condition | Responsible | Status |\n|---|---|---|---|\n"
        "| 1 | Provide hazard insurance declarations page | Borrower | Needed |\n"
        "| 2 | Title commitment updated | Borrower | Requested |\n"
        "| 3 | Letter of explanation for [PERSON_1] | Underwriter | Needed |\n"
    )
    rows = to_contract_conditions(normalize_scanned_conditions(raw))
    assert [r["num"] for r in rows] == [1, 2, 3]
    assert rows[0]["party"] == "Borrower"          # HOI override
    assert rows[1]["party"] == "Title" and rows[1]["status"] == "Requested"
    # Same as app.py: keywords say Borrower, but a non-Borrower tag from the extractor wins.
    assert rows[2]["party"] == "Underwriter"
    assert "[PERSON_1]" not in rows[2]["desc"] and "the named party" in rows[2]["desc"]


def test_quota_error_is_api_error_shape(signed_in, offline, monkeypatch):
    monkeypatch.setattr(scan_service.tiers, "check_scan_quota",
                        lambda uid, p: {"tier": "free", "tier_name": "Free", "limit": 1, "used": 1, "remaining": 0})
    with pytest.raises(ApiError):
        scan_service.check_quota(USER)

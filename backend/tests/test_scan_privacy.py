"""T-21 privacy guarantee: a scan never sends personal details or the PDF to the AI.

Builds a fake approval letter with invented personal details, records everything that would
be sent to the AI provider, and checks none of the details are in it.
"""
import pytest
from fastapi.testclient import TestClient

import cloud_client
from backend.pa_api import auth, context, scan_service
from backend.pa_api.main import app
from backend.tests.fake_pdf import make_pdf

FAKE_NAME_FIRST, FAKE_NAME_LAST = "Testy", "McFakerson"
FAKE_SSN = "123-45-6789"
FAKE_PHONE = "(555) 010-4477"
FAKE_STREET = "1234 Fakeview Lane"
FAKE_CITY = "Testville"

APPROVAL_WITH_PII = make_pdf([
    "SAMPLE LENDER (TEST DOCUMENT)",
    "Conditional Approval Letter",
    f"Borrower: {FAKE_NAME_FIRST} {FAKE_NAME_LAST}",
    f"SSN: {FAKE_SSN}",
    f"Phone: {FAKE_PHONE}",
    f"Property: {FAKE_STREET}, {FAKE_CITY}, TX 75001",
    "This loan has been approved subject to the following conditions:",
    "Prior to docs conditions",
    f"1. Provide two months of bank statements for {FAKE_NAME_FIRST} {FAKE_NAME_LAST}.",
    f"2. Letter of explanation for the credit inquiry, borrower phone {FAKE_PHONE}.",
    f"3. Hazard insurance declarations page for {FAKE_STREET}.",
    "Prior to funding conditions",
    f"4. Final verbal verification of employment. SSN on file {FAKE_SSN}.",
])

SECRETS = [FAKE_NAME_LAST, FAKE_SSN, "123456789", "010-4477", "0104477", FAKE_STREET, "Fakeview"]
USER = context.RequestContext(user_key="user-test-1", email="fake@example.test", gemini_key="AIza-fake-test-key", sandbox=False)


@pytest.fixture
def signed_in(monkeypatch):
    async def fake_context():
        with context.use(USER):
            yield USER
    app.dependency_overrides[auth.get_context] = fake_context
    # Keep the test offline: no Supabase, billing or loan store.
    monkeypatch.setattr(scan_service, "check_quota", lambda ctx: (None, {}))
    monkeypatch.setattr(scan_service, "_save_history", lambda ctx, batch: None)
    monkeypatch.setattr(scan_service, "visible_loans", lambda ctx: [])
    monkeypatch.setattr(scan_service.billing, "log_scan", lambda *a, **k: {})
    monkeypatch.setattr(scan_service.supabase_auth, "load_private_approval_intelligence", lambda *a, **k: {})
    monkeypatch.setattr(scan_service.supabase_auth, "save_private_approval_intelligence", lambda *a, **k: {"ok": True})
    monkeypatch.delenv("PA_PDF_VISION", raising=False)
    yield
    app.dependency_overrides.pop(auth.get_context, None)


@pytest.fixture
def recorded(monkeypatch):
    calls = []

    def fake_generate(prompt, system, provider, api_key, model, timeout=60):
        calls.append({"prompt": prompt, "system": system, "api_key": api_key})
        return "| # | Condition | Responsible | Status |\n|---|---|---|---|\n| 1 | Provide two months of bank statements | Borrower | Needed |"

    monkeypatch.setattr(cloud_client, "_generate", fake_generate)
    for name in ("_generate_gemini", "_generate_claude", "_generate_openai"):
        monkeypatch.setattr(cloud_client, name, lambda *a, **k: pytest.fail("AI called without going through _generate"))
    return calls


def _scan(doc_type="Approval Letter", pdf=APPROVAL_WITH_PII):
    client = TestClient(app)
    return client.post("/api/scan", data={"doc_type": doc_type},
                       files={"file": ("approval-test.pdf", pdf, "application/pdf")})


def test_ai_receives_no_personal_details(signed_in, recorded):
    response = _scan()
    assert response.status_code == 200, response.text
    assert recorded, "the AI path was not exercised; the test would prove nothing"
    for call in recorded:
        sent = f"{call['system']}\n{call['prompt']}"
        for secret in SECRETS:
            assert secret not in sent, f"personal detail reached the AI: {secret!r}"
        assert "%PDF" not in sent
        assert call["api_key"] == USER.gemini_key  # the user's own key, never a server key


def test_no_user_key_means_no_ai(signed_in, recorded, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-server-key")
    no_key = context.RequestContext(user_key="user-test-2", email="", gemini_key="", sandbox=False)

    async def ctx_without_key():
        with context.use(no_key):
            yield no_key
    app.dependency_overrides[auth.get_context] = ctx_without_key
    response = _scan()
    assert response.status_code == 200
    assert recorded == []
    assert response.json()["result"]["ai_used"] is False


def test_pdf_vision_switch_blocks_ai(signed_in, recorded, monkeypatch):
    monkeypatch.setenv("PA_PDF_VISION", "true")
    response = _scan()
    assert response.status_code == 200
    assert recorded == []


def test_response_has_no_raw_document_text(signed_in, recorded):
    body = _scan().json()
    assert "raw_text" not in str(body)
    assert FAKE_SSN not in str(body["result"]["extracted_data"])

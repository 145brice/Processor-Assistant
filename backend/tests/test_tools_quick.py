"""T-30 Quick Tools: snapshot, missing_docs, doc_expiry, report_issue, spanish_reply."""
from datetime import datetime, timedelta

import pytest

import cloud_client
from backend.pa_api import context
from backend.pa_api import models as m
from backend.pa_api.errors import ApiError
from backend.pa_api.routers import loans, tools as tools_router
from backend.tests.test_loans_visibility import temporary_pipeline  # noqa: F401  (fixture)


def ctx_for(user: str, key: str = "", sandbox: bool = False) -> context.RequestContext:
    return context.RequestContext(user, f"{user}@example.test", key, sandbox)


def run(ctx, tool, **data):
    with context.use(ctx):
        return tools_router.run_tool(tool, m.ToolIn(input=data), ctx=ctx).output


def blocks(output, kind):
    return [b for b in output["blocks"] if b["type"] == kind]


def make_loan(ctx, documents):
    import crm
    with context.use(ctx):
        loan = loans.create_loan(m.LoanCreate(loan_num="FAKE-30", borrower="Testy McFakerson", status="Pending"), ctx=ctx)
        crm.update_loan(loan.id, documents=documents)
    return loan


def iso(days_ago: int) -> str:
    return (datetime.now() - timedelta(days=days_ago)).isoformat()[:16]


# ---------- snapshot and missing docs ----------
def test_snapshot_separates_received_and_missing_and_drafts_the_email(temporary_pipeline):
    owner = ctx_for("owner")
    loan = make_loan(owner, [{"filename": "a.pdf", "doc_type": "Bank Statement", "attached": iso(1)},
                             {"filename": "b.pdf", "doc_type": "Pay Stub", "attached": iso(1)}])
    out = run(owner, "snapshot", loan_id=loan.id)
    received = next(b for b in blocks(out, "list") if b["title"] == "Received")["items"]
    missing = next(b for b in blocks(out, "list") if b["title"] == "Missing")["items"]
    assert "Bank Statement" in received and "Pay Stub" in received
    assert "1003 Application" in missing and "Bank Statement" not in missing
    email = blocks(out, "text")[0]["text"]
    assert email.startswith("The following items are needed") and "1003 Application" in email


def test_missing_docs_checklist_counts(temporary_pipeline):
    owner = ctx_for("owner")
    loan = make_loan(owner, [{"filename": "w2.pdf", "doc_type": "W-2", "attached": iso(1)}])
    out = run(owner, "missing_docs", loan_id=loan.id)
    rows = {r["label"]: r["ok"] for r in blocks(out, "checklist")[0]["rows"]}
    assert rows["W-2"] is True and rows["Appraisal"] is False
    assert len(rows) == 10                                  # the ten required document types


def test_loan_without_documents_explains_itself(temporary_pipeline):
    owner = ctx_for("owner")
    loan = make_loan(owner, [])
    assert blocks(run(owner, "missing_docs", loan_id=loan.id), "notice")


# ---------- doc expiry ----------
def test_doc_expiry_buckets(temporary_pipeline):
    owner = ctx_for("owner")
    loan = make_loan(owner, [
        {"filename": "hoi_policy.pdf", "doc_type": "Hazard Insurance", "attached": iso(400)},   # 365 days: expired
        {"filename": "voe.pdf", "doc_type": "VOE", "attached": iso(10)},                        # 30 days: 20 left
        {"filename": "appraisal.pdf", "doc_type": "Appraisal", "attached": iso(5)},             # 120 days: fine
        {"filename": "bank.pdf", "doc_type": "Bank Statement", "attached": iso(5)},             # not tracked
    ])
    out = run(owner, "doc_expiry", loan_id=loan.id)
    stats = {i["label"]: i["value"] for i in blocks(out, "stats")[0]["items"]}
    assert stats == {"Expired": 1, "Expiring soon": 1, "OK": 1}
    assert "Reminder email" in [b["title"] for b in blocks(out, "text")]


def test_filename_date_overrides_default(temporary_pipeline):
    owner = ctx_for("owner")
    when = (datetime.now() + timedelta(days=200)).strftime("%Y-%m-%d")
    loan = make_loan(owner, [{"filename": f"hoi_{when}.pdf", "doc_type": "Hazard Insurance", "attached": iso(900)}])
    stats = {i["label"]: i["value"] for i in blocks(run(owner, "doc_expiry", loan_id=loan.id), "stats")[0]["items"]}
    assert stats["OK"] == 1 and stats["Expired"] == 0


# ---------- visibility ----------
@pytest.mark.parametrize("tool", ["snapshot", "missing_docs", "doc_expiry"])
def test_other_users_loan_is_404_and_missing_loan_is_400(temporary_pipeline, tool):
    loan = make_loan(ctx_for("owner"), [])
    with pytest.raises(ApiError) as other:
        run(ctx_for("other"), tool, loan_id=loan.id)
    assert other.value.status == 404
    with pytest.raises(ApiError) as none:
        run(ctx_for("owner"), tool)
    assert none.value.status == 400


# ---------- report issue ----------
def test_report_masks_numbers_and_is_not_stored(temporary_pipeline, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = run(ctx_for("owner"), "report_issue", text="Borrower SSN 123-45-6789 and account 123456789012 failed.")
    report = next(b for b in blocks(out, "text"))["text"]
    assert "123-45-6789" not in report and "XXX-XX-6789" in report and "123456789012" not in report
    mailto = blocks(out, "link")[0]["href"]
    assert mailto.startswith("mailto:") and "123-45-6789" not in mailto
    assert list(tmp_path.iterdir()) == []                    # nothing written to disk


def test_report_needs_text(temporary_pipeline):
    with pytest.raises(ApiError) as error:
        run(ctx_for("owner"), "report_issue", text="   ")
    assert error.value.status == 400


# ---------- spanish reply ----------
def test_templates_are_local_and_need_no_key(temporary_pipeline):
    out = run(ctx_for("owner"), "spanish_reply", action="templates", conditions="1. Bank statements")
    titles = [b["title"] for b in blocks(out, "text")]
    assert any("Spanish" in t for t in titles) and any("English" in t for t in titles)
    assert "Bank statements" in blocks(out, "text")[0]["text"]


def test_english_email_gets_a_hint_not_a_translation(temporary_pipeline):
    out = run(ctx_for("owner"), "spanish_reply", action="detect", email_text="Dear borrower, please send your pay stubs.")
    assert "English email detected" in blocks(out, "notice")[0]["text"]


def test_spanish_email_without_a_key_points_to_ai_settings(temporary_pipeline):
    out = run(ctx_for("owner"), "spanish_reply", action="detect",
              email_text="Estimado señor, necesitamos los documentos de su préstamo.")
    notes = blocks(out, "notice")
    assert "Spanish email detected" in notes[0]["text"]
    assert notes[1]["href"] == "/settings/ai"


def test_translation_never_sends_personal_details(temporary_pipeline, monkeypatch):
    monkeypatch.setenv("PII_NER_MODEL", "en_core_web_md")     # what the Dockerfile sets in production
    sent = []

    def fake_generate(prompt, system, provider, api_key, model, timeout=60):
        sent.append({"prompt": prompt, "system": system, "key": api_key})
        return "Traducción: " + prompt.split(":\n\n", 1)[1]            # echo the redacted text back

    monkeypatch.setattr(cloud_client, "_generate", fake_generate)
    secret_email = ("Estimado señor, soy Testy McFakerson, mi SSN es 123-45-6789, mi teléfono es (555) 010-4477 "
                    "y mi correo es testy@example.test. Necesitamos los documentos de su préstamo.")
    owner = ctx_for("owner", key="AIza-fake-test-key")
    out = run(owner, "spanish_reply", action="detect", email_text=secret_email)

    assert sent, "the AI path was not exercised; the test would prove nothing"
    for call in sent:
        everything = f"{call['system']}\n{call['prompt']}"
        for secret in ("McFakerson", "123-45-6789", "010-4477", "testy@example.test"):
            assert secret not in everything, f"personal detail reached the AI: {secret!r}"
        assert call["key"] == "AIza-fake-test-key"
    shown = blocks(out, "text")[0]["text"]                  # the user sees the real values again
    assert "123-45-6789" in shown or "[SSN" not in shown


def test_reply_translation_needs_a_key(temporary_pipeline):
    with pytest.raises(ApiError) as error:
        run(ctx_for("owner"), "spanish_reply", action="reply", reply_en="Thank you for your email.")
    assert error.value.code == "ai_key_needed"
    with pytest.raises(ApiError) as sandbox:
        run(ctx_for("", sandbox=True), "spanish_reply", action="reply", reply_en="Thanks")
    assert sandbox.value.code == "ai_key_needed"


def test_unknown_action_is_400(temporary_pipeline):
    with pytest.raises(ApiError) as error:
        run(ctx_for("owner"), "spanish_reply", action="nope")
    assert error.value.status == 400


def test_translation_refuses_when_names_cannot_be_detected(temporary_pipeline, monkeypatch):
    """Fail closed: without the name model, free-text names would slip through, so nothing is sent."""
    monkeypatch.setenv("PII_NER_MODEL", "no_such_model")
    monkeypatch.setattr(cloud_client, "_generate", lambda *a, **k: pytest.fail("text was sent to the AI"))
    with pytest.raises(ApiError) as error:
        run(ctx_for("owner", key="AIza-fake-test-key"), "spanish_reply", action="reply", reply_en="Hello, I am Testy McFakerson.")
    assert error.value.status == 503 and error.value.code == "redaction_unavailable"

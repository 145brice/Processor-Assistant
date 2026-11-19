from io import BytesIO

import crm
import pytest
from docx import Document

from backend.pa_api import context
from backend.pa_api.errors import ApiError
from backend.pa_api.routers import loans
from backend.pa_api.main import app
from fastapi.testclient import TestClient
from backend.tests.test_loans_visibility import temporary_pipeline


def invoke(ctx, function, *args):
    with context.use(ctx):
        return function(*args, ctx=ctx)


def test_other_user_cannot_read_activity_or_drafts(temporary_pipeline):
    owner = context.RequestContext("owner", "owner@example.test", "", False)
    other = context.RequestContext("other", "other@example.test", "", False)
    with context.use(owner):
        loan = crm.add_loan("FAKE-30", "Sam Example", "Pending", "", "")
    for function in (loans.loan_activity, loans.draft_email, loans.hoi_request, loans.title_request):
        with pytest.raises(ApiError) as error:
            invoke(other, function, loan["id"])
        assert error.value.status == 404


def test_word_requests_are_valid_and_sandbox_does_not_log(temporary_pipeline):
    owner = context.RequestContext("owner", "owner@example.test", "", False)
    with context.use(owner):
        loan = crm.add_loan("FAKE-31", "Sam Example", "Pending", "", "")
    for builder in (loans.hoi_request, loans.title_request):
        response = invoke(owner, builder, loan["id"])
        document = Document(BytesIO(response.body))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        assert "Sam Example" in text
        assert "FAKE-31" in text
        assert "attachment" in response.headers["content-disposition"]
    before = crm.get_activity(loan["id"])
    sandbox = context.RequestContext("", "", "", True)
    sandbox_response = invoke(sandbox, loans.hoi_request, loan["id"])
    assert sandbox_response.status_code == 200
    assert crm.get_activity(loan["id"]) == before


def test_email_draft_omits_cleared_conditions_and_redacts_ssn(temporary_pipeline):
    owner = context.RequestContext("owner", "owner@example.test", "", False)
    with context.use(owner):
        loan = crm.add_loan("FAKE-32", "Sam Example", "Pending", "", "", conditions=[
            {"num": 1, "desc": "Cleared fake SSN 123-45-6789", "party": "Borrower", "status": "Cleared"},
            {"num": 2, "desc": "Provide fake account 1234567890 statement", "party": "Borrower", "status": "Needed"},
        ])
    draft = invoke(owner, loans.draft_email, loan["id"])
    assert "Cleared fake" not in draft.body
    assert "123-45-6789" not in draft.body
    assert "1234567890" not in draft.body


def test_document_headers_are_exposed_to_browser():
    response = TestClient(app).post("/api/loans/1/hoi-request", headers={"X-PA-Sandbox": "1", "Origin": "http://localhost:3000"})
    assert "X-PA-Gmail-URL" in response.headers["access-control-expose-headers"]
    assert "Content-Disposition" in response.headers["access-control-expose-headers"]

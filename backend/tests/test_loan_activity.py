import pytest
import crm

from backend.pa_api import context
from backend.pa_api.errors import ApiError
from backend.pa_api.routers import loans
from backend.tests.test_loans_visibility import temporary_pipeline


def invoke(ctx, function, *args):
    with context.use(ctx):
        return function(*args, ctx=ctx)


def test_other_user_cannot_read_activity_contacts_documents_or_drafts(temporary_pipeline):
    owner = context.RequestContext("owner", "owner@example.test", "", False)
    other = context.RequestContext("other", "other@example.test", "", False)
    with context.use(owner):
        loan = crm.add_loan("FAKE-30", "Sam Example", "Pending", "", "", contacts={"title": {"name": "Title Co"}})
        crm.update_loan(loan["id"], documents=[{"filename": "fake.pdf", "doc_type": "Unknown", "scanned_at": ""}])
    calls = [loans.loan_activity, loans.loan_contacts, loans.loan_documents, loans.draft_email, loans.hoi_request, loans.title_request]
    for function in calls:
        with pytest.raises(ApiError) as error:
            invoke(other, function, loan["id"])
        assert error.value.status == 404


def test_drafts_redact_stored_identifiers(temporary_pipeline):
    owner = context.RequestContext("owner", "owner@example.test", "", False)
    with context.use(owner):
        loan = crm.add_loan("FAKE-31", "Sam Example", "Pending", "", "")
        crm.update_loan(loan["id"], notes="SSN 123-45-6789 account 1234567890")
    for builder in (loans.draft_email, loans.hoi_request, loans.title_request):
        draft = invoke(owner, builder, loan["id"])
        assert "123-45-6789" not in draft.body
        assert "1234567890" not in draft.body

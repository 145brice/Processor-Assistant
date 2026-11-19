import crm
import pytest

from backend.pa_api import context
from backend.pa_api.errors import ApiError
from backend.pa_api.routers import loans
from backend.tests.test_loans_visibility import temporary_pipeline


def request_context(user: str, sandbox: bool = False):
    return context.RequestContext(user, f"{user}@example.test", "", sandbox)


def invoke(ctx, function, *args):
    with context.use(ctx):
        return function(*args, ctx=ctx)


def test_other_user_get_patch_and_conditions_are_404(temporary_pipeline):
    owner = request_context("owner")
    other = request_context("other")
    loan = invoke(owner, loans.create_loan, loans.m.LoanCreate(loan_num="FAKE-10", borrower="Taylor Example", status="Pending"))
    with pytest.raises(ApiError) as get_error:
        invoke(other, loans.get_loan, loan.id)
    assert get_error.value.status == 404
    with pytest.raises(ApiError) as patch_error:
        invoke(other, loans.update_loan, loan.id, loans.m.LoanUpdate(notes="nope"))
    assert patch_error.value.status == 404
    condition = loans.m.Condition(num=1, desc="Fake condition", party="Borrower", status="Needed")
    with pytest.raises(ApiError) as condition_error:
        invoke(other, loans.set_conditions, loan.id, loans.m.ConditionsIn(conditions=[condition]))
    assert condition_error.value.status == 404


def test_sandbox_patch_and_conditions_are_403(temporary_pipeline):
    sandbox = request_context("", True)
    with pytest.raises(ApiError) as patch_error:
        invoke(sandbox, loans.update_loan, 1, loans.m.LoanUpdate(notes="nope"))
    assert patch_error.value.status == 403
    condition = loans.m.Condition(num=1, desc="Fake condition", party="Borrower", status="Needed")
    with pytest.raises(ApiError) as condition_error:
        invoke(sandbox, loans.set_conditions, 1, loans.m.ConditionsIn(conditions=[condition]))
    assert condition_error.value.status == 403


def test_condition_save_preserves_extra_fields_and_legacy_values(temporary_pipeline):
    owner = request_context("owner")
    with context.use(owner):
        loan = crm.add_loan("FAKE-11", "Jordan Example", "Pending", "", "", conditions=[{"num": 1, "desc": "Old", "party": "Borrower", "status": "Waived", "notes": "Keep", "parties": ["Borrower"]}])
    loaded = invoke(owner, loans.get_loan, loan["id"])
    assert loaded.conditions[0].status == "Needed"
    update = loans.m.Condition(num=1, desc="New description", party="Title", status="Cleared", section="PTD")
    saved = invoke(owner, loans.set_conditions, loan["id"], loans.m.ConditionsIn(conditions=[update]))
    stored = crm.get_all_loans()[0]["conditions"][0]
    assert saved.conditions[0].status == "Cleared"
    assert stored["notes"] == "Keep"
    assert stored["parties"] == ["Borrower"]


def test_patch_notes_round_trips(temporary_pipeline):
    owner = request_context("owner")
    loan = invoke(owner, loans.create_loan, loans.m.LoanCreate(loan_num="FAKE-12", borrower="Morgan Example", status="Pending"))
    updated = invoke(owner, loans.update_loan, loan.id, loans.m.LoanUpdate(notes="Invented note"))
    assert updated.notes == "Invented note"

from backend.pa_api import context
from backend.pa_api.routers import loans


def test_list_hides_loans_owned_by_another_user(monkeypatch):
    monkeypatch.setattr("crm.get_all_loans", lambda: [
        {"id": 1, "loan_num": "FAKE-1", "borrower": "Avery Example", "status": "Pending", "owner_user_key": "user-a"},
        {"id": 2, "loan_num": "FAKE-2", "borrower": "Blair Example", "status": "Pending", "owner_user_key": "user-b"},
    ])
    result = loans.list_loans(ctx=context.RequestContext("user-a", "a@example.test", "", False))
    assert [item.id for item in result.loans] == [1]


def test_sandbox_create_is_rejected():
    body = loans.m.LoanCreate(loan_num="FAKE-3", borrower="Casey Example", status="Pending")
    try:
        loans.create_loan(body, context.RequestContext("", "", "", True))
    except loans.ApiError as error:
        assert error.status == 403
        assert error.message == "Sign in to save changes"
    else:
        raise AssertionError("sandbox write was not rejected")

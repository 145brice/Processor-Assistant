import crm

from backend.pa_api import context
from backend.pa_api.routers import loans
from backend.tests.test_loans_visibility import temporary_pipeline


def test_activity_requires_visibility_and_returns_items(temporary_pipeline):
    owner = context.RequestContext("activity-owner", "activity@example.test", "", False)
    with context.use(owner):
        loan = crm.add_loan("FAKE-20", "Riley Example", "Pending", "", "")
        crm.log_activity(loan["id"], "update", "Status changed", user="activity-owner")
    result = loans.loan_activity(loan["id"], owner)
    assert result.items[0].action == "update"

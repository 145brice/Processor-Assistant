"""T-23: merge a scan into a loan, and start a loan from a scan. Temporary pipeline, invented data."""
import pytest

from backend.pa_api import context
from backend.pa_api import models as m
from backend.pa_api.errors import ApiError
from backend.pa_api.routers import loans
from backend.tests.test_loans_visibility import temporary_pipeline  # noqa: F401  (fixture)


def ctx_for(user: str, sandbox: bool = False) -> context.RequestContext:
    return context.RequestContext(user, f"{user}@example.test", "", sandbox)


def call(ctx, function, *args):
    with context.use(ctx):
        return function(*args, ctx=ctx)


def batch(doc_type="Approval Letter", conditions=(), contacts=None, extracted=None, success=True):
    return m.ScanBatch(
        file="Fake_Doc.pdf", type=doc_type,
        result=m.ScanResult(
            success=success, doc_type=doc_type,
            conditions=[m.Condition(num=i, desc=d, party="Borrower", status="Needed") for i, d in enumerate(conditions, 1)],
            extracted_data=extracted or {}, contacts=contacts or {},
        ),
        loan_match=m.LoanMatch(),
    )


def new_loan(owner):
    loan = call(owner, loans.create_loan, m.LoanCreate(loan_num="FAKE-1", borrower="Testy McFakerson", status="Pending"))
    call(owner, loans.set_conditions, loan.id, m.ConditionsIn(conditions=[
        m.Condition(num=1, desc="Provide two months of bank statements", party="Borrower", status="Requested"),
        m.Condition(num=2, desc="Title commitment", party="Title", status="Needed"),
    ]))
    return loan


def test_merge_adds_only_new_conditions_and_renumbers(temporary_pipeline):
    owner = ctx_for("owner")
    loan = new_loan(owner)
    scan = batch(conditions=["provide two months of  BANK statements", "Hazard insurance declarations page", "Final VOE"],
                 contacts={"borrower": m.Contact(name="Testy McFakerson", phone="555-0100")})
    result = call(owner, loans.merge_scan, loan.id, m.BatchIn(batch=scan))
    assert result.added_conditions == 2                      # the bank statement one is a duplicate
    nums = [c.num for c in result.loan.conditions]
    assert nums == [1, 2, 3, 4]                              # appended after the existing 1 and 2
    assert result.loan.conditions[0].status == "Requested"   # existing condition untouched
    assert result.loan.contacts["borrower"].phone == "555-0100"
    assert [d.doc_type for d in result.loan.documents][-1] == "Approval Letter"
    assert result.loan.documents[-1].scanned_at

    again = call(owner, loans.merge_scan, loan.id, m.BatchIn(batch=scan))
    assert again.added_conditions == 0                       # merging twice never duplicates
    assert len(again.loan.conditions) == 4


def test_empty_contact_fields_never_overwrite_stored_ones(temporary_pipeline):
    owner = ctx_for("owner")
    loan = new_loan(owner)
    call(owner, loans.merge_scan, loan.id, m.BatchIn(batch=batch(contacts={"title": m.Contact(name="Fake Title Co", phone="555-0199")})))
    merged = call(owner, loans.merge_scan, loan.id, m.BatchIn(batch=batch(contacts={"title": m.Contact(name="Fake Title Co")})))
    assert merged.loan.contacts["title"].phone == "555-0199"


def test_purchase_contract_fills_closing_date_once_and_copies_agents(temporary_pipeline):
    owner = ctx_for("owner")
    loan = new_loan(owner)
    contract = batch(doc_type="Purchase Contract", extracted={
        "transaction": {"closing_date": "12/31/2099"},
        "listing_agent": {"name": "Lister Fakeagent", "phone": "555-0111"},
    })
    merged = call(owner, loans.merge_scan, loan.id, m.BatchIn(batch=contract))
    assert merged.loan.closing_date == "12/31/2099"
    assert merged.loan.contacts["listing_agent"].name == "Lister Fakeagent"

    later = batch(doc_type="Purchase Contract", extracted={"transaction": {"closing_date": "01/01/2100"}})
    again = call(owner, loans.merge_scan, loan.id, m.BatchIn(batch=later))
    assert again.loan.closing_date == "12/31/2099"           # an existing date is kept


def test_start_new_loan_from_scan(temporary_pipeline):
    owner, other = ctx_for("owner"), ctx_for("other")
    contract = batch(doc_type="Purchase Contract", conditions=["Earnest money receipt"], extracted={
        "buyer": {"name": "Buyer McFakerson"}, "transaction": {"closing_date": "12/31/2099"},
    })
    loan = call(owner, loans.loan_from_scan, m.BatchIn(batch=contract))
    assert loan.borrower == "Buyer McFakerson" and loan.loan_num == "TBD"
    assert loan.closing_date == "12/31/2099"
    assert [c.desc for c in loan.conditions] == ["Earnest money receipt"]
    assert loan.documents and loan.documents[0].doc_type == "Purchase Contract"
    assert [l.id for l in call(owner, loans.list_loans).loans] == [loan.id]
    assert call(other, loans.list_loans).loans == []         # nobody else sees it


def test_start_new_loan_needs_a_borrower_name(temporary_pipeline):
    with pytest.raises(ApiError) as error:
        call(ctx_for("owner"), loans.loan_from_scan, m.BatchIn(batch=batch(conditions=["Something"])))
    assert error.value.status == 400 and error.value.code == "no_borrower"


def test_failed_scan_cannot_be_merged(temporary_pipeline):
    owner = ctx_for("owner")
    loan = new_loan(owner)
    with pytest.raises(ApiError) as error:
        call(owner, loans.merge_scan, loan.id, m.BatchIn(batch=batch(success=False)))
    assert error.value.status == 400


def test_other_users_loan_is_404_and_sandbox_is_403(temporary_pipeline):
    loan = new_loan(ctx_for("owner"))
    with pytest.raises(ApiError) as other_error:
        call(ctx_for("other"), loans.merge_scan, loan.id, m.BatchIn(batch=batch(conditions=["x"])))
    assert other_error.value.status == 404
    sandbox = ctx_for("", sandbox=True)
    for function, args in ((loans.merge_scan, (loan.id, m.BatchIn(batch=batch()))),
                           (loans.loan_from_scan, (m.BatchIn(batch=batch()),))):
        with pytest.raises(ApiError) as sandbox_error:
            call(sandbox, function, *args)
        assert sandbox_error.value.status == 403


def test_loans_saved_by_the_streamlit_app_still_load(temporary_pipeline):
    """Regression: documents use "attached" and title contacts have no "name" in the current app."""
    import crm
    owner = ctx_for("owner")
    loan = new_loan(owner)
    with context.use(owner):
        crm.update_loan(loan.id, documents=[{"filename": "old.pdf", "doc_type": "Appraisal", "attached": "2026-01-02T03:04"}],
                        contacts={"title": {"company": "Fake Title Co", "contact": "Tess Fakeclerk", "phone": "555-0123"},
                                  "title_company": {"company": "Fake Title Co"},
                                  "seller": "Sally Fakeseller",
                                  "empty": {"phone": ""}})
    full = call(owner, loans.get_loan, loan.id)
    assert full.documents[0].scanned_at == "2026-01-02T03:04"
    assert full.contacts["title"].name == "Tess Fakeclerk" and full.contacts["title"].company == "Fake Title Co"
    assert full.contacts["title_company"].name == "Fake Title Co"
    assert full.contacts["seller"].name == "Sally Fakeseller"
    assert "empty" not in full.contacts

"""T-32 Pipeline Advanced and Automation tools."""
import json
from datetime import date, timedelta

import pytest

from backend.pa_api import context
from backend.pa_api import models as m
from backend.pa_api.errors import ApiError
from backend.pa_api.routers import loans, tools as tools_router
from backend.tests.test_loans_visibility import temporary_pipeline  # noqa: F401  (fixture)


def ctx_for(user: str) -> context.RequestContext:
    return context.RequestContext(user, f"{user}@example.test", "", False)


def run(ctx, tool, **data):
    with context.use(ctx):
        return tools_router.run_tool(tool, m.ToolIn(input=data), ctx=ctx).output


def of(output, kind):
    return [b for b in output["blocks"] if b["type"] == kind]


def stat(output, label):
    return {i["label"]: i["value"] for i in of(output, "stats")[0]["items"]}[label]


def make_loan(ctx, documents=(), **fields):
    import crm
    with context.use(ctx):
        loan = loans.create_loan(m.LoanCreate(loan_num=fields.pop("loan_num", "FAKE-32"),
                                              borrower=fields.pop("borrower", "Testy McFakerson"),
                                              status="Pending"), ctx=ctx)
        crm.update_loan(loan.id, documents=list(documents), **fields)
    return loan


def doc(filename, doc_type="", attached="2026-11-01T10:00"):
    return {"filename": filename, "doc_type": doc_type, "attached": attached}


# ---------- nothing is written to disk ----------
@pytest.mark.parametrize("tool,extra", [
    ("closing_package", {}), ("multi_borrower", {"co_borrower": "Pat Example"}), ("los_export", {"format": "csv"}),
])
def test_file_based_tools_leave_no_files_behind(temporary_pipeline, tmp_path, monkeypatch, tool, extra):
    monkeypatch.chdir(tmp_path)
    owner = ctx_for("owner")
    loan = make_loan(owner, [doc("Testy McFakerson paystub.pdf", "Pay Stub")])
    before = {p for p in tmp_path.rglob("*")}                # includes the test's own pipeline file
    run(owner, tool, loan_id=loan.id, **extra)
    created = {p for p in tmp_path.rglob("*")} - before
    assert created == set(), f"{tool} left files behind: {created}"


# ---------- closing package ----------
def test_closing_package_lists_what_is_and_is_not_in_the_loan(temporary_pipeline):
    owner = ctx_for("owner")
    loan = make_loan(owner, [doc("Closing Disclosure final.pdf", "Closing Disclosure (CD)"),
                             doc("hazard_insurance.pdf", "Hazard Insurance")])
    out = run(owner, "closing_package", loan_id=loan.id)
    rows = {r["label"]: r["ok"] for r in of(out, "checklist")[0]["rows"]}
    assert rows["Closing Disclosure (CD)"] is True and rows["Hazard Insurance"] is True
    assert rows["Survey"] is False
    assert "Testy McFakerson" in of(out, "text")[0]["text"]


# ---------- pipeline dashboard ----------
def test_dashboard_counts_only_the_callers_loans(monkeypatch):
    soon = (date.today() + timedelta(days=2)).isoformat()
    monkeypatch.setattr("crm.get_all_loans", lambda: [
        {"id": 1, "loan_num": "FAKE-32", "borrower": "Testy McFakerson", "status": "Pending", "closing_date": soon, "owner_user_key": "owner"},
        {"id": 1, "loan_num": "FAKE-99", "borrower": "Other Person", "status": "Pending", "closing_date": soon, "owner_user_key": "other"},
    ])
    out = run(ctx_for("owner"), "pipeline_dashboard")
    assert stat(out, "Total loans") == 1
    assert "FAKE-32" in str(of(out, "list")[0]) and "FAKE-99" not in str(out)       # a real closing alert, only the caller's loan
    assert stat(run(ctx_for("nobody"), "pipeline_dashboard"), "Total loans") == 0


def test_dashboard_stays_quiet_for_closed_loans_and_far_off_closings(temporary_pipeline):
    owner = ctx_for("owner")
    make_loan(owner, closing_date=(date.today() + timedelta(days=60)).isoformat())
    closed = make_loan(owner, loan_num="FAKE-33", closing_date=(date.today() + timedelta(days=1)).isoformat())
    with context.use(owner):
        loans.set_status(closed.id, m.StatusIn(status="Closed"), ctx=owner)
    out = run(owner, "pipeline_dashboard")
    assert of(out, "list") == [] and of(out, "notice")[0]["tone"] == "good"


# ---------- guidelines and fraud ----------
def test_guideline_checker_flags_a_weak_loan(temporary_pipeline):
    weak = run(ctx_for("o"), "guideline_checker", investor="fannie", dti="55", ltv="99", credit_score="560", loan_amount="400000")
    assert of(weak, "notice")[0]["tone"] == "bad" and of(weak, "list")
    strong = run(ctx_for("o"), "guideline_checker", investor="freddie", dti="30", ltv="75", credit_score="780", loan_amount="300000")
    assert of(strong, "notice")[0]["tone"] == "good"


def test_guideline_checker_rejects_an_unknown_investor(temporary_pipeline):
    with pytest.raises(ApiError) as error:
        run(ctx_for("o"), "guideline_checker", investor="ginnie")
    assert error.value.code == "bad_choice"


def test_fraud_detector_flags_what_the_module_really_checks(temporary_pipeline):
    out = run(ctx_for("o"), "fraud_detector", deposit_amount="12000", deposit_description="cash deposit",
              incomes="6000, 9500", balances="900000, 400000", monthly_income="4000")
    assert stat(out, "Flags") == 3 and stat(out, "Risk score") > 0
    text_all = str(out)
    assert "Large unexplained deposit" in text_all and "Income varies" in text_all and "high assets" in text_all.lower()


def test_fraud_detector_ignores_a_normal_deposit_and_exactly_5000(temporary_pipeline):
    for amount, note in (("12000", "payroll deposit"), ("5000", "gift")):
        out = run(ctx_for("o"), "fraud_detector", deposit_amount=amount, deposit_description=note)
        assert stat(out, "Flags") == 0 and of(out, "notice")[0]["tone"] == "good"


def test_fraud_detector_checks_the_loans_document_names(temporary_pipeline):
    owner = ctx_for("owner")
    loan = make_loan(owner, [doc("paystub_edited_copy.pdf"), doc("bank_statement.pdf")])
    out = run(owner, "fraud_detector", loan_id=loan.id)
    assert stat(out, "Flags") == 1 and "paystub_edited_copy.pdf" in str(out)


def test_fraud_detector_needs_something_to_check_and_valid_numbers(temporary_pipeline):
    with pytest.raises(ApiError) as nothing:
        run(ctx_for("o"), "fraud_detector")
    assert nothing.value.code == "missing_input"
    with pytest.raises(ApiError) as bad:
        run(ctx_for("o"), "fraud_detector", incomes="6000, lots")
    assert bad.value.code == "bad_number"


# ---------- multi-borrower ----------
def test_multi_borrower_sorts_documents_by_name(temporary_pipeline):
    owner = ctx_for("owner")
    loan = make_loan(owner, [doc("Testy McFakerson paystub.pdf"), doc("Pat Example paystub.pdf"),
                             doc("joint_1003.pdf"), doc("scan0001.pdf")])
    out = run(owner, "multi_borrower", loan_id=loan.id, co_borrower="Pat Example")
    assert (stat(out, "To primary"), stat(out, "To co-borrower"), stat(out, "Joint"), stat(out, "Unassigned")) == (1, 1, 1, 1)


# ---------- LOS export ----------
def test_los_export_csv_and_json(temporary_pipeline):
    owner = ctx_for("owner")
    loan = make_loan(owner, loan_amount="$300,000", loan_type="Conventional")
    csv_text = of(run(owner, "los_export", loan_id=loan.id, format="csv"), "text")[0]["text"]
    assert "FAKE-32" in csv_text and "Testy McFakerson" in csv_text and "300000.0" in csv_text
    parsed = json.loads(of(run(owner, "los_export", loan_id=loan.id, format="json"), "text")[0]["text"])
    assert parsed["loan_data"]["loan_id"] == "FAKE-32"


def test_los_export_never_invents_amounts(temporary_pipeline):
    owner = ctx_for("owner")
    loan = make_loan(owner)                                  # no loan amount saved
    out = run(owner, "los_export", loan_id=loan.id, format="csv")
    assert "loan_amount" not in of(out, "text")[0]["text"]
    assert "loan amount" in " ".join(of(out, "list")[0]["items"])


def test_los_export_rejects_a_bad_format(temporary_pipeline):
    owner = ctx_for("owner")
    with pytest.raises(ApiError) as error:
        run(owner, "los_export", loan_id=make_loan(owner).id, format="pdf")
    assert error.value.code == "bad_choice"


# ---------- rate lock monitor ----------
def lock(**overrides):
    base = dict(lock_date=(date.today() - timedelta(days=20)).isoformat(),
                lock_expiry_date=(date.today() + timedelta(days=10)).isoformat(),
                locked_rate="6.25", lock_days="30", current_market_rate="6.0")
    base.update(overrides)
    return base


def test_rate_lock_monitor_and_the_pipeline_lock_table(monkeypatch):
    in5, in3 = date.today() + timedelta(days=5), date.today() + timedelta(days=3)
    monkeypatch.setattr("crm.get_all_loans", lambda: [
        {"id": 1, "loan_num": "FAKE-32", "borrower": "Testy McFakerson", "lock_expiry": in5.strftime("%m/%d/%Y"), "owner_user_key": "owner"},
        {"id": 1, "loan_num": "FAKE-77", "borrower": "Other Person", "lock_expiry": in3.isoformat(), "owner_user_key": "other"},
    ])
    out = run(ctx_for("owner"), "rate_lock_monitor", **lock())
    assert stat(out, "Days until expiry") in (9, 10)
    rows = of(out, "table")[0]["rows"]
    assert [r[1] for r in rows] == ["FAKE-32"]               # only the caller's loan, never another user's
    assert rows[0][3] == "5"


@pytest.mark.parametrize("bad", [{"lock_date": "not a date"}, {"locked_rate": "abc"}, {"lock_days": "0"}])
def test_rate_lock_monitor_rejects_bad_input(temporary_pipeline, bad):
    with pytest.raises(ApiError) as error:
        run(ctx_for("o"), "rate_lock_monitor", **lock(**bad))
    assert error.value.status == 400


# ---------- underwriting tracker ----------
def test_underwriting_tracker_follows_the_loans_conditions(temporary_pipeline):
    owner = ctx_for("owner")
    loan = make_loan(owner, [doc("paystub_nov.pdf", "Pay Stub")])
    with context.use(owner):
        loans.set_conditions(loan.id, m.ConditionsIn(conditions=[
            m.Condition(num=1, desc="Provide paystub for last 30 days", party="Borrower", status="Needed"),
            m.Condition(num=2, desc="Order and provide appraisal", party="Appraiser", status="Needed")]), ctx=owner)
    out = run(owner, "underwriting_tracker", loan_id=loan.id)
    assert stat(out, "Conditions") == 2 and stat(out, "Cleared") == 0 and stat(out, "Pending") == 2
    related = next(b for b in of(out, "list") if "may clear" in b["title"])["items"]
    assert any("paystub_nov.pdf" in item for item in related)       # the pay stub is offered for the pay stub condition

    with context.use(owner):                                         # the loan marks the appraisal Cleared
        loans.set_conditions(loan.id, m.ConditionsIn(conditions=[
            m.Condition(num=2, desc="Order and provide appraisal", party="Appraiser", status="Cleared")]), ctx=owner)
    cleared = run(owner, "underwriting_tracker", loan_id=loan.id)
    assert stat(cleared, "Cleared") == 1 and stat(cleared, "Overall progress") == "50%"


def test_underwriting_tracker_with_no_conditions(temporary_pipeline):
    owner = ctx_for("owner")
    assert of(run(owner, "underwriting_tracker", loan_id=make_loan(owner).id), "notice")


# ---------- document classifier ----------
def test_document_classifier_uses_only_the_file_name(temporary_pipeline):
    out = run(ctx_for("o"), "document_classifier", filename="Jan_paystub_Testy.pdf")
    assert "Pay" in of(out, "notice")[0]["text"]
    unknown = run(ctx_for("o"), "document_classifier", filename="zzz.pdf")
    assert of(unknown, "notice")[0]["tone"] == "bad"
    with pytest.raises(ApiError):
        run(ctx_for("o"), "document_classifier", filename="  ")


# ---------- escrow calculator ----------
def test_escrow_calculator_options_change_the_total(temporary_pipeline):
    base = dict(loan_amount="300000", property_value="375000", loan_type="conventional", location="standard")
    plain_total = stat(run(ctx_for("o"), "escrow_calculator", **base), "Total closing costs")
    costly = stat(run(ctx_for("o"), "escrow_calculator", **{**base, "location": "high_cost", "include_warranty": "true"}), "Total closing costs")
    assert costly != plain_total


@pytest.mark.parametrize("bad,code", [({"loan_amount": ""}, "missing_input"), ({"escrow_months": "9"}, "out_of_range"),
                                      ({"loan_type": "jumbo"}, "bad_choice"), ({"location": "moon"}, "bad_choice")])
def test_escrow_calculator_rejects_bad_input(temporary_pipeline, bad, code):
    data = dict(loan_amount="300000", property_value="375000", loan_type="conventional", location="standard")
    data.update(bad)
    with pytest.raises(ApiError) as error:
        run(ctx_for("o"), "escrow_calculator", **data)
    assert error.value.code == code


# ---------- visibility, for every tool that takes a loan ----------
@pytest.mark.parametrize("tool,extra", [
    ("closing_package", {}), ("multi_borrower", {}), ("los_export", {"format": "csv"}), ("underwriting_tracker", {}),
])
def test_other_users_loan_is_404(temporary_pipeline, tool, extra):
    loan = make_loan(ctx_for("owner"))
    with pytest.raises(ApiError) as error:
        run(ctx_for("other"), tool, loan_id=loan.id, **extra)
    assert error.value.status == 404

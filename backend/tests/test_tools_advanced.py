"""T-31 Advanced Tools: income_verifier, auto_data_entry, credit_summary, dti_calculator,
condition_clearer, compliance_checker."""
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


def make_loan(ctx, documents):
    import crm
    with context.use(ctx):
        loan = loans.create_loan(m.LoanCreate(loan_num="FAKE-31", borrower="Testy McFakerson", status="Pending"), ctx=ctx)
        crm.update_loan(loan.id, documents=documents)
    return loan


DOC = {"filename": "paystub_jan.pdf", "doc_type": "Pay Stub", "attached": "2026-01-02T03:04",
       "extracted_data": {"borrower_name": "Testy McFakerson", "employer_name": "Fake Employer Inc",
                          "monthly_gross_income": "6000"}}


# ---------- loan-based tools ----------
@pytest.mark.parametrize("tool", ["income_verifier", "auto_data_entry"])
def test_no_saved_scan_data_says_so_instead_of_failing(temporary_pipeline, tool):
    owner = ctx_for("owner")
    out = run(owner, tool, loan_id=make_loan(owner, []).id)
    note = of(out, "notice")[0]
    assert note["tone"] == "warn" and "Scan documents into the loan" in note["text"]


def test_income_verifier_uses_the_loans_scanned_data(temporary_pipeline):
    owner = ctx_for("owner")
    out = run(owner, "income_verifier", loan_id=make_loan(owner, [DOC]).id)
    assert of(out, "stats"), "expected the match counts"
    assert of(out, "notice")[0]["text"].startswith("Status:")


def test_auto_data_entry_fills_from_the_loans_scanned_data(temporary_pipeline):
    owner = ctx_for("owner")
    out = run(owner, "auto_data_entry", loan_id=make_loan(owner, [DOC]).id)
    rows = {r["label"]: r["value"] for r in of(out, "kv")[0]["rows"]}
    assert rows["Borrower Name"] == "Testy McFakerson"
    assert rows["Employer Name"] == "Fake Employer Inc"
    assert "Completion" in [i["label"] for i in of(out, "stats")[0]["items"]]


@pytest.mark.parametrize("tool,extra", [("income_verifier", {}), ("auto_data_entry", {}),
                                        ("condition_clearer", {"condition": "Provide paystub"})])
def test_other_users_loan_is_404(temporary_pipeline, tool, extra):
    loan = make_loan(ctx_for("owner"), [DOC])
    with pytest.raises(ApiError) as error:
        run(ctx_for("other"), tool, loan_id=loan.id, **extra)
    assert error.value.status == 404


# ---------- condition clearer ----------
def test_a_matching_document_clears_the_condition(temporary_pipeline):
    owner = ctx_for("owner")
    loan = make_loan(owner, [DOC])
    out = run(owner, "condition_clearer", loan_id=loan.id, condition="Provide paystub for the last 30 days")
    assert of(out, "notice")[0]["tone"] in ("good", "warn")
    names = of(out, "list")[0]["items"]
    assert any("paystub_jan.pdf" in n for n in names)


def test_no_documents_means_nothing_to_clear_with(temporary_pipeline):
    owner = ctx_for("owner")
    out = run(owner, "condition_clearer", loan_id=make_loan(owner, []).id, condition="Provide paystub for the last 30 days")
    assert any("no scanned documents" in n["text"] for n in of(out, "notice"))


def test_condition_clearer_needs_a_condition_and_a_loan(temporary_pipeline):
    owner = ctx_for("owner")
    loan = make_loan(owner, [])
    with pytest.raises(ApiError) as no_text:
        run(owner, "condition_clearer", loan_id=loan.id, condition="  ")
    assert no_text.value.code == "missing_input"
    with pytest.raises(ApiError) as no_loan:
        run(owner, "condition_clearer", condition="Provide paystub")
    assert no_loan.value.code == "choose_loan"


# ---------- credit summary ----------
def test_credit_summary_reads_the_pasted_text(temporary_pipeline):
    out = run(ctx_for("owner"), "credit_summary", credit_text="Credit Score: 712 Experian. Account 1 open.")
    values = {i["label"]: i["value"] for i in of(out, "stats")[0]["items"]}
    assert values["Credit score"] == 712


def test_credit_summary_does_not_return_the_pasted_report(temporary_pipeline):
    report = "Credit Score: 700. Name: Testy McFakerson. SSN 123-45-6789. Account 1 open."
    out = run(ctx_for("owner"), "credit_summary", credit_text=report)
    assert "McFakerson" not in str(out) and "123-45-6789" not in str(out)


def test_credit_summary_needs_text(temporary_pipeline):
    with pytest.raises(ApiError) as error:
        run(ctx_for("owner"), "credit_summary", credit_text="")
    assert error.value.status == 400


# ---------- DTI and closing costs ----------
def test_dti_over_the_limit_is_not_qualified(temporary_pipeline):
    out = run(ctx_for("o"), "dti_calculator", action="dti", income="6000", debt="800", housing="1800", loan_type="conventional")
    assert of(out, "notice")[0]["tone"] == "bad"
    items = {i["label"]: i for i in of(out, "stats")[0]["items"]}
    assert items["Front-end DTI"]["value"].startswith("30.0%") and "limit 28.0%" in items["Front-end DTI"]["value"]


def test_dti_within_the_limit_is_qualified(temporary_pipeline):
    out = run(ctx_for("o"), "dti_calculator", action="dti", income="10000", debt="500", housing="2000", loan_type="conventional")
    assert of(out, "notice")[0]["tone"] == "good"


def test_closing_costs(temporary_pipeline):
    out = run(ctx_for("o"), "dti_calculator", action="closing", loan_amount="300,000", property_value="$375000", transaction="purchase")
    items = {i["label"]: i["value"] for i in of(out, "stats")[0]["items"]}
    assert items["LTV"] == "80.0%" and items["Total closing costs"].startswith("$")


@pytest.mark.parametrize("data,code", [
    ({"action": "dti", "income": "0"}, "bad_income"),
    ({"action": "dti", "income": "abc"}, "bad_number"),
    ({"action": "dti", "income": "-5"}, "out_of_range"),
    ({"action": "dti", "income": "5000", "loan_type": "jumbo"}, "bad_choice"),
    ({"action": "closing", "loan_amount": "0", "property_value": "100"}, "bad_amount"),
    ({"action": "closing", "loan_amount": "100"}, "missing_input"),
    ({"action": "nope"}, "unknown_action"),
])
def test_calculator_rejects_bad_input_with_a_plain_error(temporary_pipeline, data, code):
    with pytest.raises(ApiError) as error:
        run(ctx_for("o"), "dti_calculator", **data)
    assert error.value.status == 400 and error.value.code == code


# ---------- compliance ----------
def test_compliance_checker_reports_each_category(temporary_pipeline):
    out = run(ctx_for("o"), "compliance_checker", loan_type="fha", dti="52", ltv="97", credit_score="590", loan_amount="320000")
    assert of(out, "notice")[0]["text"].startswith("Overall status:")
    assert len(of(out, "list")) >= 2                       # one list per category, plus recommendations


def test_compliance_checker_validates_ranges(temporary_pipeline):
    for data in ({"dti": "101"}, {"ltv": "250"}, {"loan_type": "jumbo"}, {"credit_score": "1200"}):
        with pytest.raises(ApiError) as error:
            run(ctx_for("o"), "compliance_checker", **data)
        assert error.value.status == 400

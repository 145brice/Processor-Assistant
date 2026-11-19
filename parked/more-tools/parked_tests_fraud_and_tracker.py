"""PARKED tests for fraud_detector and underwriting_tracker (not collected by pytest: the name does not start with test_).
Copy the shared helpers (ctx_for, run, of, stat, make_loan, doc) from backend/tests/test_tools_pipeline.py when restoring."""

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

"""PARKED tests for income_verifier and auto_data_entry (not collected by pytest).
Copy the shared helpers (ctx_for, run, of, make_loan, DOC) from backend/tests/test_tools_advanced.py when restoring."""

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

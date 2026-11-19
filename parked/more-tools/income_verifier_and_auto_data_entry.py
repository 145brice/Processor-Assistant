"""PARKED, not live. Nothing imports this file.

Income Verifier and Auto Data Entry, as built for the new app (they use the data the scanner saved on a loan's documents). In the current Streamlit app both read st.session_state['scan_results'], which is set to None at start-up and never filled, so they never worked there.

To bring it back, see parked/more-tools/README.md.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

from auto_data_entry import AutoDataEntry
from income_verifier import IncomeVerifier

from backend.pa_api.context import RequestContext
from backend.pa_api.errors import ApiError
from backend.pa_api.tools import kv, listing, loan_for, notice, result, stats, tool
from backend.pa_api.tools.advanced import plain, tone_of, number


def loan_extracted(loan: dict) -> dict:
    """The data the scanner saved on this loan's documents, newest scan last."""
    merged: dict[str, Any] = {}
    for doc in loan.get("documents") or []:
        if isinstance(doc, dict) and isinstance(doc.get("extracted_data"), dict):
            merged.update(doc["extracted_data"])
    return merged


NO_DATA = ("No scanned data is saved on this loan yet. Scan documents into the loan first "
           "(open the loan, then “Scan a document into this loan”).")


# ---------- income_verifier ----------
@tool("income_verifier")
def income_verifier(ctx: RequestContext, data: dict[str, Any]) -> dict:
    loan = loan_for(ctx, data)
    extracted = loan_extracted(loan)
    if not extracted:
        return result(notice("warn", NO_DATA))
    found = IncomeVerifier().verify_income(extracted, loan)
    issues = list(found.get("income_discrepancies", [])) + list(found.get("employment_discrepancies", []))
    blocks = [
        notice(tone_of(found.get("overall_status")), f"Status: {plain(found.get('overall_status'))}"),
        stats(("Income matches", len(found.get("income_matches", [])), "good"),
              ("Income discrepancies", len(found.get("income_discrepancies", [])),
               "bad" if found.get("income_discrepancies") else "good"),
              ("Employment matches", len(found.get("employment_matches", [])), "good")),
    ]
    if issues:
        blocks.append(listing("Issues requiring attention", [str(i) for i in issues], "bad"))
    if found.get("warnings"):
        blocks.append(listing("Warnings", [str(w) for w in found["warnings"]], "warn"))
    if found.get("recommendations"):
        blocks.append(listing("Recommendations", [str(r) for r in found["recommendations"]], "info"))
    return result(*blocks)


# ---------- auto_data_entry ----------
FORM_TEMPLATE = {
    "borrower_name": "", "borrower_ssn": "", "borrower_dob": "", "monthly_gross_income": "",
    "employer_name": "", "account_number": "", "loan_amount": "",
}


@tool("auto_data_entry")
def auto_data_entry(ctx: RequestContext, data: dict[str, Any]) -> dict:
    loan = loan_for(ctx, data)
    extracted = loan_extracted(loan)
    if not extracted:
        return result(notice("warn", NO_DATA))
    filler = AutoDataEntry()
    filled = filler.fill_form(extracted, dict(FORM_TEMPLATE))
    summary = filler.get_fill_statistics(dict(FORM_TEMPLATE), filled)
    label = lambda field: field.replace("_", " ").title()  # noqa: E731
    blocks = [
        stats(("Completion", f"{summary.get('completion_percentage', 0):.0f}%", "info"),
              ("Filled", summary.get("filled_fields", 0), "good"),
              ("Total fields", summary.get("total_fields", 0), "neutral")),
        kv("Filled form fields", [(label(f), v if v else "Not filled") for f, v in filled.items()]),
    ]
    errors = filler.validate_filled_form(filled)
    if errors:
        blocks.append(listing("Validation issues", [str(e) for e in errors], "bad"))
    return result(*blocks)

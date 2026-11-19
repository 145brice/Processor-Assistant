"""Advanced Tools (task T-31): income_verifier, auto_data_entry, credit_summary, dti_calculator,
condition_clearer, compliance_checker.

Ported from the matching ``show_*_page`` functions in app.py. The engine modules are called as they
are; this file only turns their results into display blocks. Everything here is local: no tool in
this group calls an outside service.

Two differences from the current app, both because it could not work as written:
- Income Verifier and Auto Data Entry read ``st.session_state["scan_results"]``, which the
  current app sets to None at start-up and never fills, so both always answer "No extracted data".
  Here they use the data saved on the chosen loan's scanned documents.
- Condition Clearer matched against the scanner's in-memory batches (which use the keys ``file``
  and ``type``, not the ``filename`` it reads). Here it matches against the loan's documents.
"""
from __future__ import annotations

import re
from typing import Any

from auto_data_entry import AutoDataEntry
from compliance_checker import ComplianceChecker
from condition_clearer import ConditionClearer
from credit_summary import CreditSummary
from dti_calculator import DTICalculator
from income_verifier import IncomeVerifier

from ..context import RequestContext
from ..errors import ApiError
from . import kv, listing, loan_for, notice, result, stats, text_input, tool


# ---------- helpers ----------
def plain(value: Any) -> str:
    """The engine decorates statuses with emoji; drop them, the page shows colours instead."""
    return re.sub(r"^[^\w$(\[]+", "", str(value or "")).strip()


def tone_of(value: Any) -> str:
    raw = str(value or "")
    if "❌" in raw or "Fail" in raw or "Non" in raw or "Not Qualified" in raw:
        return "bad"
    if "⚠" in raw or "Partial" in raw or "Review" in raw:
        return "warn"
    if "✅" in raw or "Verified" in raw or "Compliant" in raw or "Qualified" in raw or "Cleared" in raw:
        return "good"
    return "info"


def number(data: dict[str, Any], name: str, label: str, *, minimum: float = 0.0,
           maximum: float | None = None, required: bool = True) -> float:
    raw = str(data.get(name) if data.get(name) is not None else "").strip().replace(",", "").lstrip("$")
    if not raw:
        if required:
            raise ApiError(400, "missing_input", f"{label} is required.")
        return 0.0
    try:
        value = float(raw)
    except ValueError:
        raise ApiError(400, "bad_number", f"{label} must be a number.")
    if value < minimum or (maximum is not None and value > maximum):
        limit = f"at least {minimum:g}" if maximum is None else f"between {minimum:g} and {maximum:g}"
        raise ApiError(400, "out_of_range", f"{label} must be {limit}.")
    return value


def choice(data: dict[str, Any], name: str, label: str, options: list[str], default: str) -> str:
    value = str(data.get(name) or default).strip().lower()
    if value not in options:
        raise ApiError(400, "bad_choice", f"{label} must be one of: {', '.join(options)}.")
    return value


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


# ---------- credit_summary ----------
@tool("credit_summary")
def credit_summary(ctx: RequestContext, data: dict[str, Any]) -> dict:
    report = text_input(data, "credit_text", "Credit report text", limit=300_000)
    found = CreditSummary().summarize(report)
    del report  # the pasted report is never kept; only the summary below is returned
    risk = str(found.get("risk_level", "Unknown"))
    blocks = [stats(
        ("Credit score", found.get("credit_score", "N/A"), "info"),
        ("Risk level", risk, "bad" if risk.lower() in ("high", "very high") else "good" if risk.lower() == "low" else "warn"),
        ("Accounts", found.get("total_accounts", 0), "neutral"),
    )]
    if found.get("flags"):
        blocks.append(listing("Red flags", [str(f) for f in found["flags"]], "bad"))
    if found.get("recommendations"):
        blocks.append(listing("Recommendations", [str(r) for r in found["recommendations"]], "info"))
    blocks.append(notice("neutral", str(found.get("analysis") or "No analysis available")))
    return result(*blocks)


# ---------- dti_calculator ----------
@tool("dti_calculator")
def dti_calculator(ctx: RequestContext, data: dict[str, Any]) -> dict:
    calc = DTICalculator()
    action = str(data.get("action") or "")
    if action == "dti":
        income = number(data, "income", "Monthly gross income")
        debt = number(data, "debt", "Monthly debt payments", required=False)
        housing = number(data, "housing", "Proposed housing payment", required=False)
        loan_type = choice(data, "loan_type", "Loan type", ["conventional", "fha", "va"], "conventional")
        found = calc.calculate_dti(income, debt, housing, loan_type)
        if "error" in found:
            raise ApiError(400, "bad_income", "Monthly gross income must be greater than $0.")
        qualified = bool(found.get("overall_qualified"))
        blocks = [
            notice("good" if qualified else "bad", f"Status: {plain(found.get('overall_qualified')) if not isinstance(found.get('overall_qualified'), bool) else ('Qualified' if qualified else 'Not qualified')}"),
            stats(("Front-end DTI", f"{found['front_end_dti']:.1f}% (limit {found['front_end_limit']}%)",
                   "good" if found["front_end_dti"] <= found["front_end_limit"] else "bad"),
                  ("Back-end DTI", f"{found['back_end_dti']:.1f}% (limit {found['back_end_limit']}%)",
                   "good" if found["back_end_dti"] <= found["back_end_limit"] else "bad")),
        ]
        if found.get("recommendations"):
            blocks.append(listing("Recommendations", [str(r) for r in found["recommendations"]], "info"))
        return result(*blocks)
    if action == "closing":
        amount = number(data, "loan_amount", "Loan amount")
        value = number(data, "property_value", "Property value")
        kind = choice(data, "transaction", "Transaction type", ["purchase", "refinance"], "purchase")
        found = calc.calculate_closing_costs(amount, value, kind)
        if "error" in found:
            raise ApiError(400, "bad_amount", "Loan amount must be greater than $0.")
        money = lambda x: f"${x:,.2f}"  # noqa: E731
        blocks = [stats(("Total closing costs", money(found["total_closing_costs"]), "info"),
                        ("Total cash needed", money(found["total_cash_needed"]), "neutral"),
                        ("LTV", f"{found['ltv_ratio']:.1f}%", "neutral"))]
        breakdown = found.get("breakdown")
        if isinstance(breakdown, dict) and breakdown:
            blocks.append(kv("Estimated costs", [(k.replace("_", " ").title(),
                                                  money(v) if isinstance(v, (int, float)) else v)
                                                 for k, v in breakdown.items()]))
        return result(*blocks)
    raise ApiError(400, "unknown_action", "Choose a calculation first.")


# ---------- condition_clearer ----------
@tool("condition_clearer")
def condition_clearer(ctx: RequestContext, data: dict[str, Any]) -> dict:
    condition = text_input(data, "condition", "Underwriting condition", limit=2000)
    loan = loan_for(ctx, data)
    docs = [d for d in loan.get("documents") or [] if isinstance(d, dict)]
    # The clearer looks for keys like "paystub" and "w2" inside the document type, but the scanner
    # names them "Pay Stub" and "W-2". Adding the collapsed spelling lets them match, without
    # changing the engine module.
    matchable = [
        {**d, "doc_type": f"{d.get('doc_type') or ''} {re.sub(r'[^a-z0-9]', '', str(d.get('doc_type') or '').lower())}"}
        for d in docs
    ]
    found = ConditionClearer().clear_condition(condition, matchable)
    blocks = [
        notice(tone_of(found.get("status")), f"{plain(found.get('status'))}: {found.get('reason', '')}"),
        stats(("Confidence", f"{found.get('confidence', 0)}%", tone_of(found.get("status")))),
    ]
    matches = found.get("matching_docs") or []
    if matches:
        blocks.append(listing("Matching documents",
                              [f"{m.get('filename')} ({m.get('confidence')}% match)" for m in matches], "good"))
    elif not docs:
        blocks.append(notice("info", "This loan has no scanned documents yet, so nothing can clear the condition."))
    return result(*blocks)


# ---------- compliance_checker ----------
@tool("compliance_checker")
def compliance_checker(ctx: RequestContext, data: dict[str, Any]) -> dict:
    loan_data = {
        "loan_type": choice(data, "loan_type", "Loan type", ["conventional", "fha", "va", "usda"], "conventional"),
        "dti_ratio": number(data, "dti", "DTI ratio", maximum=100, required=False),
        "ltv_ratio": number(data, "ltv", "LTV ratio", maximum=200, required=False),
        "credit_score": number(data, "credit_score", "Credit score", minimum=0, maximum=900, required=False),
        "loan_amount": number(data, "loan_amount", "Loan amount", required=False),
    }
    found = ComplianceChecker().check_compliance(loan_data)
    blocks = [
        notice(tone_of(found.get("overall_status")), f"Overall status: {plain(found.get('overall_status'))}"),
        stats(("Compliance score", f"{found.get('compliance_score', 0)}%", tone_of(found.get("overall_status")))),
    ]
    for name, category in (found.get("check_categories") or {}).items():
        flags = [plain(f) for f in category.get("flags", [])]
        title = f"{str(name).replace('_', ' ').title()}: {plain(category.get('status'))} ({category.get('score', 0)}%)"
        blocks.append(listing(title, flags or ["No issues found"], tone_of(category.get("status")) if flags else "good"))
    if found.get("recommendations"):
        blocks.append(listing("Recommendations", [str(r) for r in found["recommendations"]], "info"))
    return result(*blocks)

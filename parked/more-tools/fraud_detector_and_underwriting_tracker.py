"""PARKED, not live. Nothing imports this file.

Fraud Detector and Underwriting Tracker, as rebuilt for the new app. The current Streamlit versions could not work: the fraud page's checkboxes are ignored by the module and its sample deposit is exactly the amount it will not flag; the tracker only marks a condition cleared when the condition carries a submitted date, which that page never sends.

To bring it back, see parked/more-tools/README.md.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

from fraud_detector import FraudDetector
from underwriting_tracker import UnderwritingConditionTracker

from backend.pa_api.tools.pipeline import doc_names
from backend.pa_api.context import RequestContext
from backend.pa_api.errors import ApiError
from backend.pa_api.tools import kv, listing, loan_for, notice, result, stats, tool
from backend.pa_api.tools.advanced import plain, tone_of, number


def _numbers(data: dict[str, Any], name: str, label: str) -> list[float]:
    """A list typed as '6000, 9500' (commas, spaces or new lines)."""
    out = []
    for part in re.split(r"[,\s;]+", str(data.get(name) or "").strip()):
        if not part:
            continue
        try:
            out.append(float(part.replace("$", "").replace(",", "")))
        except ValueError:
            raise ApiError(400, "bad_number", f"{label} must be numbers separated by commas.")
    return out


@tool("fraud_detector")
def fraud_detector(ctx: RequestContext, data: dict[str, Any]) -> dict:
    """Run the module's real checks on figures the user enters and on a loan's document names.

    The current page offers three checkboxes that the module never reads (and its sample deposit
    is exactly $5,000, but the module only flags deposits over $5,000), so it can never flag
    anything. The module's checks are: deposits over $5,000 with no income-like description,
    income figures that differ by more than 20%, assets far above stated income, and document
    names that suggest alteration.
    """
    findings: dict[str, Any] = {}
    deposit = number(data, "deposit_amount", "Deposit amount", required=False)
    if deposit > 0:
        findings["deposits"] = [{"amount": deposit, "description": str(data.get("deposit_description") or "")}]
    incomes = _numbers(data, "incomes", "Income amounts")
    if incomes:
        findings["incomes"] = [{"amount": x} for x in incomes]
    balances = _numbers(data, "balances", "Account balances")
    if balances:
        findings["assets"] = [{"balance": x} for x in balances]
    monthly = number(data, "monthly_income", "Monthly income", required=False)
    if monthly > 0:
        findings["monthly_income"] = monthly
    if str(data.get("loan_id") or "").strip():
        names = [name for name, _type in doc_names(loan_for(ctx, data))]
        findings["documents"] = [{"filename": n, "content": ""} for n in names]
    if not findings:
        raise ApiError(400, "missing_input", "Enter at least one figure, or choose a loan to check its document names.")
    detector = FraudDetector()
    flags = detector.scan(findings)
    risk = detector.get_risk_score(flags)
    blocks = [stats(("Risk level", plain(risk.get("risk_level", "")), tone_of(risk.get("risk_level"))),
                    ("Risk score", risk.get("score", 0), "neutral"),
                    ("Flags", len(flags), "bad" if flags else "good"))]
    if flags:
        for severity, title, tone in (("critical", "Critical", "bad"), ("high", "High", "bad"),
                                      ("medium", "Medium", "warn"), ("low", "Low", "info")):
            picked = [f"{f.get('description')}: {f.get('recommendation')}" for f in flags if f.get("severity") == severity]
            if picked:
                blocks.append(listing(f"{title} severity", picked, tone))
    else:
        blocks.append(notice("good", "No fraud indicators found in what was checked."))
    return result(*blocks)


# ---------- underwriting_tracker ----------
def _doc_type_forms(doc_type: str) -> str:
    """Several spellings of a document type ("Pay Stub", "pay_stub", "paystub") so the tracker's
    own keywords match whichever it uses."""
    low = doc_type.lower()
    return f"{low} {re.sub(r'[^a-z0-9]+', '_', low).strip('_')} {re.sub(r'[^a-z0-9]', '', low)}".strip()


@tool("underwriting_tracker")
def underwriting_tracker(ctx: RequestContext, data: dict[str, Any]) -> dict:
    loan = loan_for(ctx, data)
    # The module marks a condition cleared only when the condition itself carries a
    # "submitted_date"; matching documents only add a confidence figure. The current page sends
    # sample conditions without one, so it can never show a cleared condition. Here a condition the
    # loan already marks Cleared counts as cleared.
    conditions = []
    for i, c in enumerate(loan.get("conditions") or [], 1):
        if not isinstance(c, dict):
            continue
        row = {"id": str(c.get("num", i)), "description": str(c.get("desc") or c.get("text") or ""),
               "due_date": str(c.get("due_date") or "")}
        if str(c.get("status") or "") == "Cleared":
            row["submitted_date"] = date.today().isoformat()
        conditions.append(row)
    submitted = [
        {"filename": str(d.get("filename") or ""), "doc_type": _doc_type_forms(str(d.get("doc_type") or "")),
         "submitted_date": str(d.get("attached") or d.get("scanned_at") or "")[:10]}
        for d in loan.get("documents") or [] if isinstance(d, dict)
    ]
    if not conditions:
        return result(notice("info", "This loan has no conditions yet."))
    found = UnderwritingConditionTracker().track_conditions(str(loan.get("loan_num") or loan.get("id")), conditions, submitted)
    blocks = [stats(("Overall progress", f"{found.get('overall_progress', 0):.0f}%", "info"),
                    ("Conditions", found.get("total_conditions", 0), "neutral"),
                    ("Cleared", found.get("cleared_conditions", 0), "good"),
                    ("Pending", found.get("pending_conditions", 0), "warn"))]
    tones = {"cleared": "good", "pending": "warn", "overdue": "bad"}
    for status in ("overdue", "pending", "cleared"):
        rows = [c for c in found.get("condition_status", []) if c.get("status") == status]
        if rows:
            blocks.append(listing(f"{status.title()} ({len(rows)})", [str(c.get("description")) for c in rows], tones[status]))
    related = [
        f"{c.get('description')}: {', '.join(str(d.get('filename')) for d in c.get('document_details', []))}"
        for c in found.get("condition_status", [])
        if c.get("status") != "cleared" and c.get("document_details")
    ]
    if related:
        blocks.append(listing("Documents on the loan that may clear pending conditions", related, "info"))
    return result(*blocks)

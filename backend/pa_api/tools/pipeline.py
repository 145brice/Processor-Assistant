"""Pipeline Advanced and Automation tools (task T-32): closing_package, pipeline_dashboard,
guideline_checker, fraud_detector, multi_borrower, los_export, rate_lock_monitor,
underwriting_tracker, document_classifier, escrow_calculator.

Ported from the matching ``show_*_page`` functions in app.py. Everything here is local: no tool
calls an outside service. Four of the engine modules read or write folders on disk
(closing_package, multi_borrower, los_export, document_classifier). The API stores no files, so
those tools use only the pure parts of the module (matching file names, building text) on the
loan's saved document list, or run in a throw-away temporary folder that is deleted at once.

The current app's versions of several pages are demos: multi-borrower, LOS export, rate lock
monitor and underwriting tracker run on hard-coded sample data, and fraud detector asks for its
three findings as checkboxes. Where a real loan can feed the tool it does here; the fraud detector
keeps its checkboxes because the module has nothing else to read.
"""
from __future__ import annotations

import csv
import io
import json
import re
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

from closing_package import ClosingPackageGenerator
from document_classifier import AutomatedDocumentClassifier
from escrow_calculator import EscrowCalculator
from fraud_detector import FraudDetector
from guideline_checker import GuidelineChecker
from los_export import LOSExport
from multi_borrower import MultiBorrowerHandler
from pipeline_dashboard import PipelineDashboard
from rate_lock_monitor import RateLockMonitor
from underwriting_tracker import UnderwritingConditionTracker

from ..context import RequestContext
from ..errors import ApiError
from . import (
    checklist, flag, kv, listing, loan_for, notice, result, stats, table, text, text_input, tool,
    visible_loans,
)
from .advanced import choice, number, plain, tone_of

SEVERITY_TONE = {"low": "info", "medium": "warn", "high": "bad", "critical": "bad"}


def doc_names(loan: dict) -> list[tuple[str, str]]:
    """(filename, doc_type) for each document saved on the loan."""
    return [(str(d.get("filename") or ""), str(d.get("doc_type") or ""))
            for d in loan.get("documents") or [] if isinstance(d, dict)]


# ---------- closing_package ----------
@tool("closing_package")
def closing_package(ctx: RequestContext, data: dict[str, Any]) -> dict:
    """The closing package checklist and manifest for a loan.

    The current page copies files into a "Closing_Package" folder. With no stored files there is
    nothing to copy, so this lists which closing documents are in the loan and which are missing,
    and gives the manifest text.
    """
    loan = loan_for(ctx, data)
    generator = ClosingPackageGenerator()
    found: dict[str, list[dict]] = {}
    for filename, doc_type in doc_names(loan):
        kind = generator._identify_document_type(f"{filename} {doc_type}".lower())
        found.setdefault(kind, []).append({"name": filename, "path": ""})
    missing = generator._check_missing_documents(found)
    required = generator.required_closing_docs
    blocks = [
        stats(("Required", len(required), "neutral"), ("In the loan", len(required) - len(missing), "good"),
              ("Missing", len(missing), "bad" if missing else "good")),
        checklist("Closing documents", [(name, name not in missing) for name in required]),
        text("Package manifest", generator._create_manifest(
            found, str(loan.get("borrower") or ""), datetime.now().strftime("%Y%m%d_%H%M"))),
    ]
    if not found:
        blocks.insert(0, notice("info", "No documents have been scanned into this loan yet."))
    return result(*blocks)


# ---------- pipeline_dashboard ----------
def _for_dashboard(loan: dict) -> dict:
    """Give a stored loan the field names PipelineDashboard reads.

    The module looks for ``days_to_close``, ``stage``, ``created_date``, ``last_activity_date``,
    ``lock_expiry_date`` and ``loan_number``, which stored loans do not have (they keep
    ``closing_date``, ``status``, ``created``, ``updated``, ``lock_expiry`` and ``loan_num``). Without
    this mapping the dashboard never raises a closing alert. Closed loans raise none.
    """
    out = dict(loan)
    closed = loan.get("status") == "Closed"
    closing = _parse_day(loan.get("closing_date"))
    if closing and not closed:
        out["days_to_close"] = (closing - date.today()).days
    expires = _parse_day(loan.get("lock_expiry"))
    if expires and not closed:
        out["lock_expiry_date"] = expires.isoformat()
    out["stage"] = loan.get("status") or "Unknown"
    out["loan_number"] = loan.get("loan_num")
    out["borrower_name"] = loan.get("borrower")
    out["created_date"] = str(loan.get("created") or "")
    out["last_activity_date"] = "" if closed else str(loan.get("updated") or "")
    out["loan_amount"] = _amount(loan.get("loan_amount")) or 0
    return out


@tool("pipeline_dashboard")
def pipeline_dashboard(ctx: RequestContext, data: dict[str, Any]) -> dict:
    loans = [_for_dashboard(loan) for loan in visible_loans(ctx)]
    dashboard = PipelineDashboard()
    alerts = dashboard.get_alerts(loans)
    summary = dashboard.get_pipeline_summary(loans)
    blocks = [stats(
        ("Total loans", summary.get("total_loans", 0), "neutral"),
        ("Closing this week", summary.get("closing_this_week", 0), "warn" if summary.get("closing_this_week") else "good"),
        ("Closing this month", summary.get("closing_this_month", 0), "info"),
        ("Avg days in pipeline", f"{summary.get('average_days_in_pipeline', 0):.1f}", "neutral"),
    )]
    for key, title, tone in (("urgent", "Urgent (closing within 3 days, or lock about to expire)", "bad"),
                             ("expired", "Rate lock expired", "bad"),
                             ("warning", "Warning (closing within 7 days)", "warn"),
                             ("stale", "No recent activity", "warn"),
                             ("notice", "Notice (closing within 14 days)", "info")):
        if alerts.get(key):
            blocks.append(listing(title, [plain(a.get("message", "")) for a in alerts[key]], tone))
    if not alerts.get("total"):
        blocks.append(notice("good", "No closing deadlines, expired locks or stale loans right now."))
    return result(*blocks)


# ---------- guideline_checker ----------
@tool("guideline_checker")
def guideline_checker(ctx: RequestContext, data: dict[str, Any]) -> dict:
    investor = choice(data, "investor", "Investor", ["fannie", "freddie"], "fannie")
    loan_data = {
        "dti_ratio": number(data, "dti", "DTI ratio", maximum=100, required=False),
        "ltv_ratio": number(data, "ltv", "LTV ratio", maximum=200, required=False),
        "credit_score": number(data, "credit_score", "Credit score", maximum=900, required=False),
        "loan_amount": number(data, "loan_amount", "Loan amount", required=False),
    }
    found = GuidelineChecker(investor).check(loan_data)
    blocks = [notice("good" if found.get("passed") else "bad",
                     f"{plain(found.get('status'))}. " + ("Loan meets all guidelines."
                                                         if found.get("passed") else "Loan does not meet guidelines: review required."))]
    if found.get("flags"):
        blocks.append(listing("Issues found", [plain(f) for f in found["flags"]], "bad"))
    if found.get("warnings"):
        blocks.append(listing("Warnings", [plain(w) for w in found["warnings"]], "warn"))
    return result(*blocks)


# ---------- fraud_detector ----------
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


# ---------- multi_borrower ----------
@tool("multi_borrower")
def multi_borrower(ctx: RequestContext, data: dict[str, Any]) -> dict:
    """Sort a loan's documents between the borrower, a co-borrower and joint documents.

    Uses only the module's naming rules. The module's own ``process`` also creates folders on disk,
    which the API never does.
    """
    loan = loan_for(ctx, data)
    primary = str(loan.get("borrower") or "").strip()
    if not primary:
        raise ApiError(400, "no_borrower", "This loan has no borrower name.")
    co = text_input(data, "co_borrower", "Co-borrower name", required=False, limit=200) or None
    files = [name for name, _type in doc_names(loan)]
    found = MultiBorrowerHandler()._assign_documents_to_borrowers(files, primary, co)
    assigned = found.get("assigned", {})
    blocks = [stats(("To primary", len(assigned.get("primary", [])), "info"),
                    ("To co-borrower", len(assigned.get("co_borrower", [])), "info"),
                    ("Joint", len(assigned.get("joint", [])), "neutral"),
                    ("Unassigned", len(found.get("unassigned", [])), "warn" if found.get("unassigned") else "good"))]
    for key, title in (("primary", f"Primary borrower ({primary})"), ("co_borrower", f"Co-borrower ({co or 'none'})"),
                       ("joint", "Joint documents")):
        if assigned.get(key):
            blocks.append(listing(title, [str(f) for f in assigned[key]], "neutral"))
    if found.get("unassigned"):
        blocks.append(listing("Not matched to anyone", [str(f) for f in found["unassigned"]], "warn"))
    if not files:
        blocks.insert(0, notice("info", "No documents have been scanned into this loan yet."))
    return result(*blocks)


# ---------- los_export ----------
def _amount(value: Any) -> float | None:
    cleaned = re.sub(r"[^0-9.]", "", str(value or ""))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


@tool("los_export")
def los_export(ctx: RequestContext, data: dict[str, Any]) -> dict:
    """The loan's data as CSV or JSON text for a loan origination system.

    The module writes files to a folder; that happens in a temporary folder that is removed
    straight away, and only the text is returned.
    """
    loan = loan_for(ctx, data)
    fmt = choice(data, "format", "Export format", ["csv", "json"], "csv")
    loan_data = {
        "loan_id": str(loan.get("loan_num") or loan.get("id")),
        "borrower_name": str(loan.get("borrower") or ""),
        "loan_type": str(loan.get("loan_type") or ""),
        "property_address": str(loan.get("property_address") or ""),
        "lender": str(loan.get("lender") or ""),
        "status": str(loan.get("status") or ""),
        "closing_date": str(loan.get("closing_date") or ""),
        "lock_expiry": str(loan.get("lock_expiry") or ""),
    }
    # Amounts the loan does not have are left out, never exported as zero.
    for key, source in (("loan_amount", "loan_amount"), ("property_value", "purchase_price")):
        value = _amount(loan.get(source))
        if value is not None:
            loan_data[key] = value
    exporter = LOSExport()
    with tempfile.TemporaryDirectory() as directory:
        done = exporter.export(loan_data, directory, fmt)
        if not done.get("success"):
            raise ApiError(400, "export_failed", "The export could not be created: " + "; ".join(map(str, done.get("errors", []))))
        produced = [Path(p) for p in done.get("files_created", []) if str(p).lower().endswith("." + fmt)]
        content = produced[0].read_text(encoding="utf-8-sig") if produced else ""
    blocks = [text(f"{fmt.upper()} export for loan {loan_data['loan_id']}", content)]
    compat = exporter.validate_los_compatibility(loan_data)
    missing = [str(f).replace("_", " ") for f in compat.get("missing_fields", [])]
    if missing:
        blocks.append(listing(
            f"Fields a loan origination system expects that this loan does not have "
            f"(data quality {compat.get('data_quality_score', 0)}%)", missing, "warn"))
    return result(*blocks)


# ---------- rate_lock_monitor ----------
def _parse_day(value: Any) -> date | None:
    raw = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(raw[:10] if fmt == "%Y-%m-%d" else raw, fmt).date()
        except ValueError:
            continue
    return None


def _day_input(data: dict[str, Any], name: str, label: str) -> str:
    raw = str(data.get(name) or "").strip()
    if _parse_day(raw) is None:
        raise ApiError(400, "bad_date", f"{label} must be a date.")
    return _parse_day(raw).isoformat()


@tool("rate_lock_monitor")
def rate_lock_monitor(ctx: RequestContext, data: dict[str, Any]) -> dict:
    lock = {
        "lock_date": _day_input(data, "lock_date", "Lock date"),
        "lock_expiry_date": _day_input(data, "lock_expiry_date", "Lock expiry date"),
        "locked_rate": number(data, "locked_rate", "Locked rate (%)", maximum=30),
        "lock_days": int(number(data, "lock_days", "Lock days", minimum=1, maximum=365)),
        "current_market_rate": number(data, "current_market_rate", "Current market rate (%)", maximum=30),
    }
    found = RateLockMonitor().monitor_lock(lock)
    blocks = [
        notice(tone_of(found.get("status")), f"Lock status: {plain(found.get('status'))}"),
        stats(("Days until expiry", found.get("days_until_expiry", 0), "info"),
              ("Locked rate", f"{found.get('locked_rate', 0):.2f}%", "neutral"),
              ("Float-down available", "Yes" if found.get("float_down_available") else "No", "neutral")),
    ]
    alerts = found.get("alerts") or []
    for kind, title, tone in (("critical", "Critical alerts", "bad"), ("warning", "Warnings", "warn")):
        picked = [str(a.get("message")) for a in alerts if a.get("type") == kind]
        if picked:
            blocks.append(listing(title, picked, tone))
    other = [str(a.get("message")) for a in alerts if a.get("type") not in ("critical", "warning")]
    if other:
        blocks.append(listing("Notices", other, "info"))
    if found.get("recommendations"):
        blocks.append(listing("Recommendations", [str(r) for r in found["recommendations"]], "info"))
    # The locks already on the caller's loans, soonest first.
    today = date.today()
    rows = []
    for loan in visible_loans(ctx):
        expires = _parse_day(loan.get("lock_expiry"))
        if expires:
            rows.append((expires, loan))
    if rows:
        rows.sort(key=lambda pair: pair[0])
        blocks.append(table("Locks in your pipeline", ["Borrower", "Loan", "Lock expires", "Days left"],
                            [[l.get("borrower"), l.get("loan_num"), d.isoformat(), (d - today).days] for d, l in rows[:25]]))
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


# ---------- document_classifier ----------
@tool("document_classifier")
def document_classifier(ctx: RequestContext, data: dict[str, Any]) -> dict:
    """Classify a document by its file name. Nothing is uploaded or read; only the name is used."""
    name = text_input(data, "filename", "File name", limit=300)
    found = AutomatedDocumentClassifier().classify_document(name)
    label = lambda s: str(s).replace("_", " ").title()  # noqa: E731
    if not found.get("primary_classification"):
        return result(notice("bad", "Document type not recognized from the file name."))
    blocks = [
        notice("good", f"Classified as {label(found['primary_classification'])}."),
        stats(("Confidence", f"{found.get('confidence', 0)}%", "info"),
              ("Routing folder", label(found.get("routing_folder", "")), "neutral")),
    ]
    if found.get("secondary_classifications"):
        blocks.append(listing("Could also be", [label(s) for s in found["secondary_classifications"]], "neutral"))
    if found.get("recommendations"):
        blocks.append(listing("Recommendations", [str(r) for r in found["recommendations"]], "info"))
    return result(*blocks)


# ---------- escrow_calculator ----------
@tool("escrow_calculator")
def escrow_calculator(ctx: RequestContext, data: dict[str, Any]) -> dict:
    tax = number(data, "annual_tax", "Annual property tax", required=False)
    insurance = number(data, "annual_insurance", "Annual hazard insurance", required=False)
    loan_data = {
        "loan_amount": number(data, "loan_amount", "Loan amount"),
        "property_value": number(data, "property_value", "Property value"),
        "loan_type": choice(data, "loan_type", "Loan type", ["conventional", "fha", "va"], "conventional"),
        "location": choice(data, "location", "Location", ["standard", "high_cost", "low_cost"], "standard"),
        "include_home_warranty": flag(data, "include_warranty"),
        "escrow_months": int(number(data, "escrow_months", "Escrow months", minimum=1, maximum=6, required=False) or 2),
    }
    # Leave these out when blank so the calculator uses its own estimate. The engine treats a key
    # that is present but None as a value and crashes; the current page sends None and crashes too.
    if tax > 0:
        loan_data["annual_property_tax"] = tax
    if insurance > 0:
        loan_data["annual_hazard_insurance"] = insurance
    found = EscrowCalculator().calculate_closing_costs(loan_data)
    if "error" in found:
        raise ApiError(400, "bad_amount", str(found["error"]))
    money = lambda x: f"${x:,.2f}"  # noqa: E731
    blocks = [stats(("Total closing costs", money(found["total_closing_costs"]), "info"),
                    ("Total cash needed", money(found["total_cash_needed"]), "neutral"),
                    ("Cost-to-loan ratio", f"{found['cost_to_loan_ratio']:.1f}%", "neutral"))]
    breakdown = found.get("breakdown")
    if isinstance(breakdown, dict) and breakdown:
        blocks.append(kv("Cost breakdown", [(k.replace("_", " ").title(), money(v) if isinstance(v, (int, float)) else v)
                                            for k, v in breakdown.items()]))
    return result(*blocks)

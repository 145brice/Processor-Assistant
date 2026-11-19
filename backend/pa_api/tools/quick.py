"""Quick Tools (task T-30): snapshot, report_issue, missing_docs, doc_expiry, spanish_reply.

Ported from show_snapshot_page, show_report_issue_page, show_missing_docs_page,
show_doc_expiry_page and show_spanish_reply_page in app.py. The current app reads a folder of
saved documents on disk (``loan_docs/<id>``). The API stores no documents, so these tools work
from the document list saved on each loan (what the scanner recorded), exactly like the
current Snapshot page does when a loan has no folder.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote

import doc_expiry_tracker
import feedback_reporter
import loan_snapshot
import spanish_reply

from ..context import RequestContext
from ..errors import ApiError
from . import (
    checklist, link, listing, loan_for, notice, result, stats, text, text_input, tool,
)
from .translate import translate

REQUIREMENTS = loan_snapshot.DOCUMENT_REQUIREMENTS
SUPPORT_EMAIL = "info@edgelandings.com"  # the privacy-policy contact


# ---------- shared: which required documents does a loan have? ----------
def present_types(loan: dict) -> set[str]:
    """Same alias matching as the current Snapshot page."""
    present: set[str] = set()
    for doc in loan.get("documents") or []:
        if not isinstance(doc, dict):
            continue
        kind = str(doc.get("doc_type") or doc.get("type") or "").lower()
        for required, info in REQUIREMENTS.items():
            aliases = [a.lower() for a in info.get("aliases", [])] + [required.lower()]
            if any(alias in kind for alias in aliases):
                present.add(required)
    return present


def snapshot_for(loan: dict) -> dict:
    present = present_types(loan)
    complete = [{"document": name, "files": []} for name in REQUIREMENTS if name in present]
    missing = [{"document": name, "required": True} for name, info in REQUIREMENTS.items()
               if name not in present and info.get("required")]
    return {
        "loan_folder": loan.get("borrower", ""),
        "complete": complete, "missing": missing, "stale": [], "partial": [],
        "complete_count": len(complete), "missing_count": len(missing),
        "stale_count": 0, "partial_count": 0,
    }


# ---------- snapshot ----------
@tool("snapshot")
def snapshot(ctx: RequestContext, data: dict[str, Any]) -> dict:
    loan = loan_for(ctx, data)
    snap = snapshot_for(loan)
    blocks = [stats(
        ("Complete", snap["complete_count"], "good"),
        ("Missing", snap["missing_count"], "bad" if snap["missing_count"] else "good"),
    )]
    if snap["missing"]:
        blocks.append(listing("Missing", [m["document"] for m in snap["missing"]], "bad"))
    if snap["complete"]:
        blocks.append(listing("Received", [c["document"] for c in snap["complete"]], "good"))
    if snap["missing"]:
        blocks.append(text("Missing documents email", loan_snapshot.get_missing_docs_email_body(snap)))
    else:
        blocks.append(notice("good", "All required documents have been received."))
    return result(*blocks)


# ---------- missing_docs ----------
@tool("missing_docs")
def missing_docs(ctx: RequestContext, data: dict[str, Any]) -> dict:
    loan = loan_for(ctx, data)
    present = present_types(loan)
    required = [name for name, info in REQUIREMENTS.items() if info.get("required")]
    rows = [(name, name in present) for name in required]
    missing = [name for name, ok in rows if not ok]
    blocks = [
        stats(("Required", len(required), "neutral"), ("Received", len(required) - len(missing), "good"),
              ("Missing", len(missing), "bad" if missing else "good")),
        checklist("Required documents", rows),
    ]
    if not (loan.get("documents") or []):
        blocks.append(notice("info", "No documents have been scanned into this loan yet. "
                                     "Scan documents into the loan to track them here."))
    return result(*blocks)


# ---------- doc_expiry ----------
_EXPIRY_KINDS = {
    "insurance": ["insurance", "hoi", "hazard", "policy"],
    "appraisal": ["appraisal", " appraisal", "1004", "1075"],
    "credit_report": ["credit", "tri-merge"],
    "title": ["title", "commitment", "prelim"],
    "voe": ["voe", "verification of employment"],
}


def _attached(doc: dict) -> datetime:
    raw = str(doc.get("attached") or doc.get("scanned_at") or "")
    try:
        return datetime.fromisoformat(raw[:19])
    except ValueError:
        return datetime.now()


def expiry_rows(loan: dict) -> list[dict]:
    """Tracked documents with their expiry. The attach date stands in for the file date."""
    rows = []
    for doc in loan.get("documents") or []:
        if not isinstance(doc, dict):
            continue
        name = str(doc.get("filename") or doc.get("doc_type") or "Document")
        haystack = f"{name} {doc.get('doc_type') or ''}".lower()
        kind = next((k for k, words in _EXPIRY_KINDS.items() if any(w in haystack for w in words)), None)
        if kind is None:
            continue
        expires = doc_expiry_tracker.parse_expiry_from_filename(name) or (
            _attached(doc) + timedelta(days=doc_expiry_tracker.get_default_expiry_days(kind)))
        rows.append({"name": name, "days": (expires - datetime.now()).days})
    return rows


@tool("doc_expiry")
def doc_expiry(ctx: RequestContext, data: dict[str, Any]) -> dict:
    rows = expiry_rows(loan_for(ctx, data))
    expired = [r for r in rows if r["days"] < 0]
    soon = [r for r in rows if 0 <= r["days"] <= 30]
    fine = [r for r in rows if r["days"] > 30]
    blocks = [stats(("Expired", len(expired), "bad" if expired else "good"),
                    ("Expiring soon", len(soon), "warn" if soon else "good"),
                    ("OK", len(fine), "good"))]
    if expired:
        blocks.append(listing("Expired", [r["name"] for r in expired], "bad"))
    if soon:
        blocks.append(listing("Expiring soon", [f"{r['name']} ({r['days']} days)" for r in soon], "warn"))
    if fine:
        blocks.append(listing("OK", [f"{r['name']} ({r['days']} days)" for r in fine], "good"))
    if not rows:
        blocks.append(notice("info", "No tracked documents found for this loan. Insurance, appraisal, "
                                     "credit report, title and VOE documents are tracked."))
    if expired or soon:
        body = "The following documents need attention:\n\n"
        if expired:
            body += "EXPIRED:\n" + "".join(f"  - {r['name']}\n" for r in expired) + "\n"
        if soon:
            body += "Expiring Soon:\n" + "".join(
                f"  - {r['name']} (expires in {r['days']} days)\n" for r in soon) + "\n"
        blocks.append(text("Reminder email", body + "Please provide updated documents."))
    return result(*blocks)


# ---------- report_issue ----------
@tool("report_issue")
def report_issue(ctx: RequestContext, data: dict[str, Any]) -> dict:
    """Mask sensitive numbers and hand the user a report to send. Nothing is stored.

    The current app saves the report to a folder on the machine it runs on; on a web server that
    folder is not the user's, so the masked report is given back to copy or email instead.
    """
    notes = text_input(data, "text", "Describe the problem")
    loan_label = ""
    if str(data.get("loan_id") or "").strip():
        loan_label = f"Loan: {loan_for(ctx, data).get('loan_num', '')}\n"
    masked = feedback_reporter.mask_all_sensitive(notes)
    report = (f"Processor Assistant issue report\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
              f"{loan_label}\n{masked}")
    mailto = f"mailto:{SUPPORT_EMAIL}?subject={quote('Processor Assistant issue report')}&body={quote(report)}"
    return result(
        notice("info", "Social Security and bank account numbers are masked to the last 4 digits. "
                       "Nothing is stored on our servers."),
        text("Your report (masked)", report),
        link("Email this report", mailto),
    )


# ---------- spanish_reply ----------
@tool("spanish_reply")
def spanish_reply_tool(ctx: RequestContext, data: dict[str, Any]) -> dict:
    action = str(data.get("action") or "")
    if action == "detect":
        email = text_input(data, "email_text", "Email text")
        found = spanish_reply.detect_language(email)
        if not found.is_spanish:
            return result(notice("info", "English email detected. Use “Generate templates” to draft "
                                         "Spanish and English replies."))
        # The engine's confidence is a word ratio times 10 and is not capped (it can read 700%).
        blocks = [notice("info", f"Spanish email detected ({min(found.confidence, 1.0):.0%} confidence).")]
        try:
            blocks.append(text("English translation", translate(ctx, email, "English")))
        except ApiError as error:
            if error.status != 400:
                raise
            blocks.append(notice("warn", error.message,
                                 "/settings/ai" if error.code == "ai_key_needed" else "", "AI Settings"))
        return result(*blocks)
    if action == "reply":
        reply = text_input(data, "reply_en", "Your reply in English")
        return result(text("Spanish email draft (ready to copy to Gmail)", translate(ctx, reply, "Spanish")))
    if action == "templates":
        conditions = text_input(data, "conditions", "Conditions", required=False)
        blocks = [
            text("Spanish email template (ready to send to the borrower)", spanish_reply.get_spanish_template(conditions)),
            text("English email template (for reference)", spanish_reply.get_english_template(conditions)),
        ]
        if not conditions:
            blocks.insert(0, notice("info", "Add conditions to personalize the templates."))
        return result(*blocks)
    raise ApiError(400, "unknown_action", "Choose what to do first.")

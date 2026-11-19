"""Put a scan result into the pipeline (task T-23).

Same rules as the Streamlit scanner's loan-match actions in app.py `show_dashboard`:

- Merge into Loan: add scanned conditions whose description is not already on the loan, merge
  contacts (non-empty values win), merge the title company contact, and for a Purchase Contract
  fill the closing/due date when the loan has none and copy the listing/selling agents.
  The scan is recorded with crm.attach_document (metadata only, never the PDF).
- Start New Loan: borrower from the purchase contract buyer or the first named contact, loan
  number "TBD", closing date from the contract, the scanned conditions and contacts.

One deliberate difference: merged conditions are renumbered to follow the loan's existing ones,
because PUT /api/loans/{id}/conditions (T-25) matches conditions by number.
"""
from __future__ import annotations

from typing import Any

from . import models as m
from .context import RequestContext
from .errors import ApiError


# ---------- copied from app.py (_normalize_title_contact and friends) ----------
def _normalize_title_contact(*sources) -> dict:
    out: dict[str, str] = {}
    for source in sources:
        if not source:
            continue
        if isinstance(source, str):
            source = {"company": source}
        if not isinstance(source, dict):
            continue
        company = (source.get("company") or source.get("title_company") or source.get("name")
                   or source.get("settlement_agent") or source.get("escrow_company") or "")
        contact = source.get("contact") or source.get("contact_name") or source.get("agent") or ""
        phone = source.get("phone") or source.get("contact_phone") or ""
        email = source.get("email") or source.get("contact_email") or ""
        for key, value in (("company", company), ("contact", contact), ("phone", phone), ("email", email)):
            if value and not out.get(key):
                out[key] = value
    return {k: v for k, v in out.items() if str(v).strip()}


def _title_contact_from_scan_result(result: dict) -> dict:
    extracted = result.get("extracted_data") or {}
    contacts = result.get("contacts") or {}
    return _normalize_title_contact(
        extracted.get("title"), extracted.get("title_company"), extracted.get("settlement_agent"),
        contacts.get("title"), contacts.get("title_company"), contacts.get("settlement_agent"),
    )


def _merge_title_contact_into_contacts(contacts: dict, title_contact: dict) -> dict:
    contacts = dict(contacts or {})
    title_contact = _normalize_title_contact(title_contact)
    if not title_contact:
        return contacts
    merged = dict(_normalize_title_contact(contacts.get("title"), contacts.get("title_company"),
                                           contacts.get("settlement_agent")))
    for key, value in title_contact.items():
        if value and not merged.get(key):
            merged[key] = value
    contacts["title"] = merged
    contacts["title_company"] = merged
    return contacts


# ---------- helpers ----------
def _clean_contacts(raw: Any) -> dict[str, dict]:
    """Contract contacts with empty fields dropped, so they never overwrite stored values."""
    out: dict[str, dict] = {}
    for role, value in (raw or {}).items():
        if isinstance(value, dict):
            kept = {k: v for k, v in value.items() if v not in (None, "")}
            if kept:
                out[str(role)] = kept
    return out


def _desc_key(desc: Any) -> str:
    return " ".join(str(desc or "").split()).casefold()


def _next_num(conditions: list[dict]) -> int:
    nums = []
    for cond in conditions:
        try:
            nums.append(int(cond.get("num")))
        except (TypeError, ValueError):
            continue
    return max(nums, default=len(conditions)) + 1


def borrower_from_batch(batch: m.ScanBatch) -> str:
    data = batch.result.extracted_data or {}
    buyer = data.get("buyer") if isinstance(data, dict) else None
    if isinstance(buyer, dict) and buyer.get("name"):
        return str(buyer["name"]).strip()
    for contact in batch.result.contacts.values():
        if contact.name.strip():
            return contact.name.strip()
    return ""


def _closing_date(batch: m.ScanBatch) -> str:
    data = batch.result.extracted_data or {}
    txn = data.get("transaction") if isinstance(data, dict) else None
    return str(txn.get("closing_date") or "") if isinstance(txn, dict) else ""


# ---------- actions ----------
def merge_scan(ctx: RequestContext, loan: dict, batch: m.ScanBatch) -> int:
    """Merge `batch` into `loan` (already checked as visible to ctx). Returns conditions added."""
    import crm

    if not batch.result.success:
        raise ApiError(400, "scan_failed", "This scan has no results to merge.")
    result = batch.result.model_dump()
    existing = [dict(c) for c in (loan.get("conditions") or []) if isinstance(c, dict)]
    seen = {_desc_key(c.get("desc") or c.get("text")) for c in existing}
    number = _next_num(existing)
    added = 0
    for cond in result["conditions"]:
        key = _desc_key(cond.get("desc"))
        if not key or key in seen:
            continue
        seen.add(key)
        new = {k: v for k, v in cond.items() if v is not None}
        new["num"] = number
        number += 1
        existing.append(new)
        added += 1

    contacts = dict(loan.get("contacts") or {})
    contacts.update(_clean_contacts(result["contacts"]))
    title_contact = _title_contact_from_scan_result(result)
    contacts = _merge_title_contact_into_contacts(contacts, title_contact)

    changes: dict[str, Any] = {"conditions": existing, "contacts": contacts}
    if batch.type == "Purchase Contract":
        data = result.get("extracted_data") or {}
        closing = _closing_date(batch)
        if closing and not loan.get("closing_date"):
            changes["closing_date"] = closing
            changes["due_date"] = closing
        for role in ("listing_agent", "selling_agent"):
            agent = data.get(role)
            if isinstance(agent, dict) and any(agent.values()):
                contacts[role] = agent
        changes["contacts"] = _merge_title_contact_into_contacts(contacts, title_contact)
        message = "Purchase Contract merged contacts & dates updated"
    else:
        message = f"{batch.type} scanned {added} condition(s) merged"

    loan_id = int(loan["id"])
    crm.update_loan(loan_id, **changes)
    crm.attach_document(loan_id, batch.file, batch.type, extracted=result.get("extracted_data") or None)
    crm.log_activity(loan_id, "upload", message, user=ctx.email)
    return added


def loan_from_scan(ctx: RequestContext, batch: m.ScanBatch) -> dict:
    """Create a loan from a scan the way 'Start New Loan from this Doc' does. Returns the loan."""
    import crm

    if not batch.result.success:
        raise ApiError(400, "scan_failed", "This scan has no results to start a loan from.")
    borrower = borrower_from_batch(batch)
    if not borrower:
        raise ApiError(400, "no_borrower", "This document has no borrower name, so a loan can't be started from it.")
    result = batch.result.model_dump()
    closing = _closing_date(batch)
    conditions = [{k: v for k, v in c.items() if v is not None} for c in result["conditions"]]
    loan = crm.add_loan(
        loan_num=batch.loan_match.loan_num or "TBD",
        borrower=borrower,
        status="Pending",
        due_date=closing,
        missing_docs="",
        folder_path="",
        closing_date=closing,
        conditions=conditions,
        contacts=_clean_contacts(result["contacts"]),
        created_by=ctx.email,
    )
    loan_id = int(loan["id"])
    if ctx.user_key:
        crm.update_loan(loan_id, assigned_user_key=ctx.user_key)
    crm.attach_document(loan_id, batch.file, batch.type, extracted=result.get("extracted_data") or None)
    crm.log_activity(loan_id, "created", f"Loan created from scanned {batch.type}", user=ctx.email)
    return loan

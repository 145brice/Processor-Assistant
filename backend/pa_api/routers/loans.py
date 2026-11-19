"""Pipeline and loan endpoints. Fixed paths are declared before /loans/{loan_id}."""
from __future__ import annotations

import csv
import io
import json
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, UploadFile

from .. import models as m
from ..auth import get_context
from ..context import RequestContext
from ..errors import ApiError, NotBuilt

router = APIRouter(prefix="/api/loans", tags=["loans"])

Sort = Literal["newest", "borrower", "close", "lock", "loan_num", "status"]
VALID_STATUSES = {"Pending", "Requested", "Cleared", "Overdue", "Closed"}
VALID_CONDITION_STATUSES = {"Needed", "Requested", "Important", "Ready to Clear", "Cleared"}


def _loan_keys(loan: dict) -> set[str]:
    keys = {str(loan.get(name, "")).strip() for name in ("owner_user_key", "created_by_user_key", "assigned_user_key")}
    shared = loan.get("shared_with_user_keys", [])
    if isinstance(shared, str):
        try:
            shared = json.loads(shared)
        except (TypeError, ValueError):
            shared = [shared]
    if isinstance(shared, list):
        keys.update(str(value).strip() for value in shared)
    return {key for key in keys if key}


def _visible(loan: dict, ctx: RequestContext) -> bool:
    return ctx.sandbox or bool(ctx.user_key and ctx.user_key in _loan_keys(loan))


def _write_context(ctx: RequestContext) -> None:
    if ctx.sandbox:
        raise ApiError(403, "sandbox_write", "Sign in to save changes")


def _summary(loan: dict) -> m.LoanSummary:
    conditions = loan.get("conditions") or []
    cleared = sum(1 for condition in conditions if condition.get("status") == "Cleared")
    progress = round(cleared * 100 / len(conditions)) if conditions else 0
    normalized_status = loan.get("status") if loan.get("status") in VALID_STATUSES else "Pending"
    return m.LoanSummary(
        id=int(loan.get("id", 0)), loan_num=str(loan.get("loan_num", "")), borrower=str(loan.get("borrower", "")),
        status=normalized_status, closing_date=str(loan.get("closing_date", "")),
        lock_expiry=str(loan.get("lock_expiry", "")), lock_expired=bool(loan.get("lock_expired", False)),
        missing_docs=str(loan.get("missing_docs", "")), assigned_to=str(loan.get("assigned_to", "")),
        progress_percent=progress, contacts_line=str(loan.get("contacts_line", "")), updated=str(loan.get("updated", "")),
    )


def _full(loan: dict) -> m.Loan:
    data = dict(loan)
    if data.get("status") not in VALID_STATUSES:
        data["status"] = "Pending"
    data["progress_percent"] = _summary(loan).progress_percent
    for field in ("loan_amount", "purchase_price"):
        if data.get(field) is not None:
            data[field] = str(data[field])
    normalized_conditions = []
    for index, condition in enumerate(data.get("conditions") or [], start=1):
        item = dict(condition)
        try:
            item["num"] = int(item.get("num", index))
        except (TypeError, ValueError):
            item["num"] = index
        item["desc"] = item.get("desc") or item.get("text", "")
        party = item.get("party", "")
        item["party"] = ", ".join(party) if isinstance(party, list) else str(party)
        if item.get("status") not in VALID_CONDITION_STATUSES:
            item["status"] = "Needed"
        normalized_conditions.append(item)
    data["conditions"] = normalized_conditions
    return m.Loan.model_validate(data)


def _find(loan_id: int, ctx: RequestContext) -> dict:
    import crm
    for loan in crm.get_all_loans() or []:
        if int(loan.get("id", -1)) == loan_id and _visible(loan, ctx):
            return loan
    raise ApiError(404, "not_found", "Loan not found")


def _safe_text(value: object) -> str:
    import re
    text = str(value or "")
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b", "[redacted]", text)
    return re.sub(r"\b(?:account|acct)[\s:#-]*\d{4,}\b", "account [redacted]", text, flags=re.I)


def _draft(loan: dict, kind: str) -> m.TextDraft:
    borrower = _safe_text(loan.get("borrower"))
    number = _safe_text(loan.get("loan_num"))
    address = _safe_text(loan.get("property_address"))
    if kind == "email":
        subject = f"Loan {number} - outstanding conditions"
        body = f"Hello,\n\nPlease provide the outstanding items for loan {number} for {borrower}.\n"
        body += "\n".join(f"- {_safe_text(item.get('desc') or item.get('text'))}" for item in loan.get("conditions", []))
    elif kind == "hoi":
        subject = f"HOI / Evidence of Insurance Request Loan {number}"
        body = f"Please provide Evidence of Insurance for loan {number}.\nBorrower: {borrower}\nProperty: {address}\n"
    else:
        subject = f"Title Work Request Loan {number}"
        body = f"Please provide title work for loan {number}.\nBorrower: {borrower}\nProperty: {address}\n"
    return m.TextDraft(subject=subject, body=_safe_text(body))


@router.get("", response_model=m.LoanList)
def list_loans(
    status: Optional[m.LoanStatus] = None,
    q: Optional[str] = None,
    sort: Sort = "newest",
    mine: bool = False,
    ctx: RequestContext = Depends(get_context),
) -> m.LoanList:
    import crm
    loans = [loan for loan in (crm.get_all_loans() or []) if _visible(loan, ctx)]
    if status:
        loans = [loan for loan in loans if loan.get("status") == status]
    if q:
        needle = q.casefold()
        loans = [loan for loan in loans if needle in str(loan.get("loan_num", "")).casefold() or needle in str(loan.get("borrower", "")).casefold()]
    if mine:
        loans = [loan for loan in loans if ctx.user_key and ctx.user_key in {str(loan.get("assigned_user_key", "")), str(loan.get("owner_user_key", ""))}]
    sort_key = {"borrower": lambda x: str(x.get("borrower", "")).casefold(), "close": lambda x: x.get("closing_date", ""), "lock": lambda x: x.get("lock_expiry", ""), "loan_num": lambda x: x.get("loan_num", ""), "status": lambda x: x.get("status", "")}.get(sort, lambda x: x.get("updated", ""))
    loans.sort(key=sort_key, reverse=sort == "newest")
    counts = {name: sum(1 for loan in [x for x in (crm.get_all_loans() or []) if _visible(x, ctx)] if name == "all" or loan.get("status") == name.title()) for name in ("all", "pending", "requested", "cleared", "overdue", "closed")}
    return m.LoanList(loans=[_summary(loan) for loan in loans], counts=m.StatusCounts(**counts))


@router.post("", response_model=m.Loan)
def create_loan(body: m.LoanCreate, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    _write_context(ctx)
    import crm
    loan = crm.add_loan(body.loan_num, body.borrower, body.status, body.due_date or "", body.missing_docs or "", created_by=ctx.email, assigned_to=body.assigned_to or "", lock_expiry=body.lock_expiry or "", closing_date=body.closing_date or "")
    return _full(loan)


@router.get("/removed", response_model=m.RemovedLoans)
def removed_loans(ctx: RequestContext = Depends(get_context)) -> m.RemovedLoans:
    import crm
    return m.RemovedLoans(loans=[_summary(loan) for loan in (crm.get_trash() or []) if _visible(loan, ctx)], retention_days=crm.get_retention_days())


@router.post("/import", response_model=m.ImportResult)
async def import_loans(file: UploadFile = File(...), ctx: RequestContext = Depends(get_context)) -> m.ImportResult:
    _write_context(ctx)
    content = await file.read()
    try:
        if file.filename and file.filename.lower().endswith(".json"):
            rows = json.loads(content.decode("utf-8"))
        else:
            rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
        if not isinstance(rows, list):
            raise ValueError
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ApiError(400, "invalid_import", "Upload a valid CSV or JSON pipeline file.")
    import crm
    result = crm.bulk_import_loans(rows, created_by=ctx.email, assigned_to="")
    return m.ImportResult(imported=result.get("added", 0), skipped=result.get("skipped", 0), errors=result.get("errors", []))


@router.post("/from-scan", response_model=m.Loan)
def loan_from_scan(body: m.BatchIn, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    raise NotBuilt("T-23")


@router.get("/{loan_id}/contacts")
def loan_contacts(loan_id: int, ctx: RequestContext = Depends(get_context)) -> dict:
    return {"contacts": _find(loan_id, ctx).get("contacts", {}) or {}}


@router.get("/{loan_id}/documents")
def loan_documents(loan_id: int, ctx: RequestContext = Depends(get_context)) -> dict:
    return {"documents": _find(loan_id, ctx).get("documents", []) or []}


@router.post("/{loan_id}/draft-email", response_model=m.TextDraft)
def draft_email(loan_id: int, ctx: RequestContext = Depends(get_context)) -> m.TextDraft:
    return _draft(_find(loan_id, ctx), "email")


@router.post("/{loan_id}/hoi-request", response_model=m.TextDraft)
def hoi_request(loan_id: int, ctx: RequestContext = Depends(get_context)) -> m.TextDraft:
    return _draft(_find(loan_id, ctx), "hoi")


@router.post("/{loan_id}/title-request", response_model=m.TextDraft)
def title_request(loan_id: int, ctx: RequestContext = Depends(get_context)) -> m.TextDraft:
    return _draft(_find(loan_id, ctx), "title")


@router.get("/{loan_id}", response_model=m.Loan)
def get_loan(loan_id: int, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    return _full(_find(loan_id, ctx))


@router.patch("/{loan_id}", response_model=m.Loan)
def update_loan(loan_id: int, body: m.LoanUpdate, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    _write_context(ctx)
    loan = _find(loan_id, ctx)
    import crm
    changes = body.model_dump(exclude_none=True)
    crm.update_loan(loan_id, **changes)
    return _full(_find(loan_id, ctx))


@router.delete("/{loan_id}", response_model=m.Ok)
def delete_loan(loan_id: int, ctx: RequestContext = Depends(get_context)) -> m.Ok:
    _write_context(ctx)
    import crm
    _find(loan_id, ctx)
    crm.delete_loan(loan_id)
    return m.Ok(ok=True)


@router.post("/{loan_id}/status", response_model=m.Loan)
def set_status(loan_id: int, body: m.StatusIn, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    _write_context(ctx)
    import crm
    _find(loan_id, ctx)
    crm.set_status(loan_id, body.status)
    return _full(_find(loan_id, ctx))


@router.put("/{loan_id}/conditions", response_model=m.Loan)
def set_conditions(loan_id: int, body: m.ConditionsIn, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    _write_context(ctx)
    loan = _find(loan_id, ctx)
    import crm
    stored = loan.get("conditions") or []
    incoming_by_num = {condition.num: condition for condition in body.conditions}
    merged = []
    for existing in stored:
        try:
            num = int(existing.get("num"))
        except (TypeError, ValueError):
            merged.append(existing)
            continue
        condition = incoming_by_num.get(num)
        if condition is None:
            merged.append(existing)
            continue
        updated = dict(existing)
        updated.update({
            "desc": condition.desc,
            "party": condition.party,
            "status": condition.status,
            "section": condition.section,
        })
        merged.append(updated)
    known = {int(item.get("num")) for item in stored if str(item.get("num", "")).isdigit()}
    merged.extend(condition.model_dump() for condition in body.conditions if condition.num not in known)
    crm.update_loan(loan_id, conditions=merged)
    return _full(_find(loan_id, ctx))


@router.post("/{loan_id}/restore", response_model=m.Loan)
def restore_loan(loan_id: int, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    _write_context(ctx)
    import crm
    loan = next((item for item in crm.get_trash() or [] if int(item.get("id", -1)) == loan_id and _visible(item, ctx)), None)
    if not loan:
        raise ApiError(404, "not_found", "Loan not found")
    crm.restore_loan(loan_id)
    return _full(_find(loan_id, ctx))


@router.post("/{loan_id}/merge-scan", response_model=m.MergeResult)
def merge_scan(loan_id: int, body: m.BatchIn, ctx: RequestContext = Depends(get_context)) -> m.MergeResult:
    raise NotBuilt("T-23")


@router.get("/{loan_id}/activity", response_model=m.ActivityList)
def loan_activity(loan_id: int, ctx: RequestContext = Depends(get_context)) -> m.ActivityList:
    _find(loan_id, ctx)
    import crm
    items = []
    for item in crm.get_activity(loan_id) or []:
        normalized = dict(item)
        normalized["at"] = normalized.get("at") or normalized.get("ts", "")
        items.append(m.Activity.model_validate(normalized))
    return m.ActivityList(items=items)

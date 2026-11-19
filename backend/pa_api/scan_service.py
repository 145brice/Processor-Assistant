"""One document scan for POST /api/scan (task T-21).

Same steps as the Streamlit scan loop in app.py `show_dashboard`:
quota -> ai_engine.process_document -> normalise conditions -> approval intelligence ->
borrower match against the caller's own loans -> billing.log_scan -> scan history.

Privacy (RULES.md section 1):
- The PDF bytes go only to ai_engine.process_document, which extracts text locally. AI is
  reached only through cloud_client's redacting functions, and only with the caller's own key.
- AI is refused outright if the old PA_PDF_VISION opt-in is ever switched on.
- Raw document text stays on the server: it is used for borrower matching and then dropped.
  Nothing from the document is logged.
"""
from __future__ import annotations

import logging
import os
import secrets
import time
from typing import Any, get_args

import ai_engine
import approval_intelligence
import billing
import scan_history_store
import supabase_auth
import tiers
from doc_verify import _match_borrower

from . import models as m
from .context import RequestContext
from .errors import ApiError
from .normalize import normalize_scanned_conditions, to_contract_conditions

log = logging.getLogger("pa_api.scan")

AI_DOC_TYPES = {"Approval Letter", "Purchase Contract"}
TIER_KEYS = set(get_args(m.TierKey))


# ---------- who is scanning ----------
def is_owner(email: str) -> bool:
    """Owner accounts skip the scan quota. Set PA_OWNER_ADMIN_EMAILS (comma separated)."""
    owners = {e.strip().lower() for e in os.getenv("PA_OWNER_ADMIN_EMAILS", "").split(",") if e.strip()}
    return bool(email) and email.strip().lower() in owners


def pdf_vision_enabled() -> bool:
    return os.getenv("PA_PDF_VISION", "false").strip().lower() in ("1", "true", "yes", "on")


def ai_allowed(ctx: RequestContext, doc_type: str) -> bool:
    return bool(ctx.gemini_key) and not ctx.sandbox and doc_type in AI_DOC_TYPES and not pdf_vision_enabled()


def _profile(ctx: RequestContext) -> dict:
    if is_owner(ctx.email):
        return {"subscription_status": "active"}
    try:
        return supabase_auth.ensure_user_profile(ctx.user_key, email=ctx.email) or {}
    except Exception:
        return {}


def usage_summary(quota: dict, profile: dict) -> m.UsageSummary:
    tier = quota.get("tier") if quota.get("tier") in TIER_KEYS else "free"
    return m.UsageSummary(
        tier=tier,
        tier_name=str(quota.get("tier_name") or ""),
        limit=quota.get("limit"),
        used=int(quota.get("used") or 0),
        remaining=quota.get("remaining"),
        free_beta=bool(tiers.free_beta_mode() or profile.get("beta_free") is True),
    )


def check_quota(ctx: RequestContext) -> tuple[dict | None, dict]:
    """Raise 402 when the monthly limit is used up. Sandbox and owners are not limited."""
    if ctx.sandbox or not ctx.user_key or is_owner(ctx.email):
        return None, {}
    profile = _profile(ctx)
    quota = tiers.check_scan_quota(ctx.user_key, profile)
    if quota.get("limit") is not None and int(quota.get("used") or 0) >= int(quota["limit"]):
        upgrade = f" Upgrade to {quota['next_tier_name']} for more." if quota.get("next_tier_name") else ""
        raise ApiError(402, "scan_limit_reached",
                       f"You've used all {quota['limit']} scans on your {quota.get('tier_name', 'current')} plan this month.{upgrade}")
    return quota, profile


# ---------- loans the caller may see ----------
def _loan_user_keys(loan: dict) -> set[str]:
    """Copied from app.py `_loan_user_keys`."""
    keys = {str(loan.get(f) or "").strip() for f in ("owner_user_key", "created_by_user_key", "assigned_user_key")}
    shared = loan.get("shared_with_user_keys", [])
    if isinstance(shared, str):
        try:
            import json
            shared = json.loads(shared)
        except Exception:
            shared = [shared]
    if isinstance(shared, list):
        keys.update(str(v).strip() for v in shared)
    keys.discard("")
    return keys


def visible_loans(ctx: RequestContext) -> list[dict]:
    """Sandbox sees demo loans; real accounts only loans tied to them (app.py `_visible_account_loans`)."""
    try:
        from crm import get_all_loans
        loans = get_all_loans() or []
    except Exception:
        return []
    if ctx.sandbox:
        return loans
    if not ctx.user_key:
        return []
    return [loan for loan in loans if ctx.user_key in _loan_user_keys(loan)]


def loan_match(ctx: RequestContext, raw_text: str, filename: str, contacts: dict) -> m.LoanMatch:
    hint = next((c["name"] for c in contacts.values() if isinstance(c, dict) and c.get("name")), "")
    loans = visible_loans(ctx)
    if not loans:
        return m.LoanMatch()
    try:
        found = _match_borrower(raw_text, filename, hint, loans=loans) or {}
    except Exception:
        return m.LoanMatch()
    ids = {loan.get("id") for loan in loans}
    if found.get("loan_id") not in ids:
        return m.LoanMatch()
    suggestion = found.get("suggestion") if found.get("suggestion") in ("match", "possible", "unknown") else "unknown"
    return m.LoanMatch(
        loan_id=int(found["loan_id"]),
        loan_num=str(found.get("loan_num") or ""),
        borrower=str(found.get("borrower") or ""),
        confidence=int(found.get("confidence") or 0),
        suggestion=suggestion,
    )


# ---------- result shaping ----------
def _contacts(raw: Any) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not isinstance(raw, dict):
        return out
    for role, value in raw.items():
        if isinstance(value, str):
            value = {"name": value}
        if not isinstance(value, dict) or not str(value.get("name") or "").strip():
            continue
        out[str(role)] = {
            "name": str(value["name"]).strip(),
            "company": str(value.get("company") or value.get("brokerage") or "") or None,
            "phone": str(value.get("phone") or "") or None,
            "email": str(value.get("email") or "") or None,
            "role": str(value.get("role") or "") or None,
        }
    return out


def _extracted(result: dict) -> dict:
    data = result.get("extracted_data")
    if not isinstance(data, dict) or not data:
        data = result.get("bank_fields") if isinstance(result.get("bank_fields"), dict) else {}
    cleaned = scan_history_store.parsed_batch(data)  # drops raw text and bytes, keeps JSON values
    return {k: v for k, v in cleaned.items() if not str(k).startswith("_")}


def _ai_outcome(ctx: RequestContext, doc_type: str, approved: bool, result: dict) -> tuple[bool, str]:
    note = str(result.get("ai_log") or "").lower()
    failed = any(w in note for w in ("skip", "fail", "error", "block", "disabled", "exception"))
    if approved and result.get("success") and note and not failed:
        return True, "Enhanced with Gemini using redacted text only"
    if approved:
        return False, "Local extraction only. AI enhancement was not available for this scan."
    if doc_type in AI_DOC_TYPES and not ctx.sandbox and not ctx.gemini_key:
        return False, "Local extraction only. Add your Gemini API key for AI-enhanced results."
    return False, "Local extraction"


def _apply_approval_intelligence(ctx: RequestContext, result: dict, rows: list[dict]) -> list[dict]:
    """Party ownership learned from this processor's own approvals (app.py does the same).

    Stores only the de-identified aggregates that approval_intelligence.normalize_state keeps.
    """
    try:
        state: dict = {}
        if ctx.user_key and not ctx.sandbox:
            state = supabase_auth.load_private_approval_intelligence(ctx.user_key) or {}
        state = approval_intelligence.normalize_state(state)
        raw_text = result.get("raw_text", "") or result.get("bank_raw_text", "") or ""
        lender = approval_intelligence.detect_lender_name(raw_text)
        rows = approval_intelligence.apply_ownership(rows, state)
        state, _summary = approval_intelligence.record_scan(state, lender, rows, extraction_succeeded=bool(rows))
        if ctx.user_key and not ctx.sandbox:
            supabase_auth.save_private_approval_intelligence(
                ctx.user_key, approval_intelligence.normalize_state(state), user_email=ctx.email)
    except Exception as exc:
        log.warning("approval intelligence skipped: %s", type(exc).__name__)
    return rows


def _save_history(ctx: RequestContext, batch: dict) -> None:
    if ctx.sandbox or not ctx.user_key:
        return
    loaded = scan_history_store.load(ctx.user_key)
    if not loaded.get("ok"):
        log.warning("scan history not saved: history could not be loaded")
        return
    entry = {"id": secrets.token_hex(16), "ts": time.time(), "user_key": ctx.user_key,
             "batch": scan_history_store.parsed_batch(batch)}
    saved = scan_history_store.save(ctx.user_key, [entry] + loaded["items"], ctx.email)
    if not saved.get("ok"):
        log.warning("scan history not saved: save failed")


# ---------- the scan ----------
def run_scan(ctx: RequestContext, filename: str, pdf_bytes: bytes, doc_type: str) -> m.ScanResponse:
    quota, profile = check_quota(ctx)
    approved = ai_allowed(ctx, doc_type)
    started = time.monotonic()

    try:
        result = ai_engine.process_document(pdf_bytes, doc_type, user_approved_cloud=approved) or {}
    except Exception as exc:
        log.warning("scan failed: doc_type=%s error=%s", doc_type, type(exc).__name__)
        result = {"success": False, "error": "This document could not be read. Try another copy of the PDF."}

    success = bool(result.get("success"))
    contacts = _contacts(result.get("contacts"))
    rows = normalize_scanned_conditions(result.get("conditions")) if success else []
    if success and doc_type == "Approval Letter":
        rows = _apply_approval_intelligence(ctx, result, rows)
    ai_used, ai_note = _ai_outcome(ctx, doc_type, approved, result)

    scan_result = m.ScanResult(
        success=success,
        doc_type=doc_type,
        conditions=to_contract_conditions(rows),
        extracted_data=_extracted(result) if success else {},
        contacts=contacts,
        risks=str(result.get("risks") or result.get("bank_rules") or "") if success else "",
        image_only=bool(result.get("image_only")),
        ai_used=ai_used,
        ai_note=ai_note,
        error="" if success else str(result.get("error") or "This document could not be read."),
    )
    match = loan_match(ctx, str(result.get("raw_text") or result.get("bank_raw_text") or ""), filename, contacts) if success else m.LoanMatch()
    del result  # raw document text is not kept beyond this point

    usage = None
    if success:
        if not ctx.sandbox and ctx.user_key:
            try:
                billing.log_scan(ctx.user_key, doc_type)
            except Exception as exc:
                log.warning("scan not logged for billing: %s", type(exc).__name__)
        batch = {"file": filename, "type": doc_type, "result": scan_result.model_dump(), "loan_match": match.model_dump()}
        _save_history(ctx, batch)
    if quota is not None:
        try:
            usage = usage_summary(tiers.check_scan_quota(ctx.user_key, profile), profile)
        except Exception:
            usage = None

    log.info("scan done: doc_type=%s success=%s ai=%s seconds=%.1f", doc_type, success, ai_used, time.monotonic() - started)
    return m.ScanResponse(file=filename, type=doc_type, result=scan_result, loan_match=match, usage=usage)

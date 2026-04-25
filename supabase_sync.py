"""
Supabase backup mirror.

- Local SQLite + JSON files are PRIMARY (always authoritative).
- Supabase is a backup mirror only. Never blocks the app.
- Writes are batched (60s flush, max 50 records/batch, dedupe by key).
- Hard cap: 100 calls/hour. Auto-pauses on overage.
- Sandbox mode = no calls. Sync paused via session_state = no calls.
- Sensitive fields (SSN, DOB, account#, routing#, license#, extracted_data, PDFs)
  are stripped before every upload.
"""
import os
import json
import time
import threading
import hashlib
from datetime import datetime, timezone
from typing import Any

# ─────────────────────────── Config ───────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

_FLUSH_INTERVAL_SEC = 60
_MAX_BATCH_SIZE = 50
_HOURLY_CALL_CAP = 100

_SENSITIVE_KEYS = {
    "ssn", "social_security_number", "social_security",
    "dob", "date_of_birth", "birth_date", "birthdate",
    "account_number", "account_no", "acct_number",
    "routing_number", "routing_no",
    "license_number", "drivers_license", "dl_number",
    "extracted_data", "pdf_bytes", "pdf_data", "raw_text",
}

_SYNC_STATE_FILE = os.path.join(os.path.dirname(__file__), "sync_state.json")
_SYNC_ERROR_LOG = os.path.join(os.path.dirname(__file__), "sync_errors.json")

# ─────────────────────────── State ───────────────────────────
_client = None
_client_init_attempted = False
_queue: dict = {}  # key=(table, record_id) -> latest record dict
_queue_lock = threading.Lock()
_call_log: list = []  # timestamps of recent calls (for hourly cap)
_call_log_lock = threading.Lock()
_last_flush_ts = 0.0
_record_hashes: dict = {}  # key=(table, id) -> hash of last successfully sent record
_flush_thread = None
_flush_thread_started = False
_paused = False


# ─────────────────────────── Public API ───────────────────────────
def is_enabled() -> bool:
    """True if Supabase is configured and not paused."""
    if _paused:
        return False
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    return _get_client() is not None


def is_paused() -> bool:
    return _paused


def set_paused(paused: bool):
    global _paused
    _paused = bool(paused)
    _save_state()


def get_status() -> dict:
    """Status dict for the UI."""
    state = _load_state()
    with _queue_lock:
        queue_size = len(_queue)
    with _call_log_lock:
        recent_calls = len([t for t in _call_log if time.time() - t < 3600])
    return {
        "enabled": is_enabled(),
        "paused": _paused,
        "configured": bool(SUPABASE_URL and SUPABASE_KEY),
        "last_flush": state.get("last_flush"),
        "last_error": state.get("last_error"),
        "queue_size": queue_size,
        "calls_last_hour": recent_calls,
        "hourly_cap": _HOURLY_CALL_CAP,
    }


def mirror_loan(loan: dict):
    """Queue a loan record for backup."""
    if not is_enabled() or not loan or not loan.get("id"):
        return
    redacted = _redact(loan)
    record = {
        "id": loan["id"],
        "loan_num": redacted.get("loan_num"),
        "borrower": redacted.get("borrower"),
        "property_address": redacted.get("property_address"),
        "status": redacted.get("status"),
        "lender": redacted.get("lender"),
        "loan_amount": _to_str(redacted.get("loan_amount")),
        "purchase_price": _to_str(redacted.get("purchase_price")),
        "loan_type": redacted.get("loan_type"),
        "closing_date": redacted.get("closing_date"),
        "loan_officer": redacted.get("loan_officer"),
        "loan_processor": redacted.get("loan_processor"),
        "contacts_json": json.dumps(_redact(loan.get("contacts", {}) or {})),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _enqueue("loans", record["id"], record)
    _ensure_flush_thread()


def mirror_loans_bulk(loans: list):
    """Queue multiple loans at once (used after bulk pipeline saves)."""
    if not is_enabled() or not loans:
        return
    for loan in loans:
        mirror_loan(loan)


def mirror_user(user: dict):
    """Queue a user account for backup."""
    if not is_enabled() or not user or not user.get("id"):
        return
    record = {
        "id": str(user["id"]),
        "email": user.get("email"),
        "password_hash": user.get("password_hash"),
        "display_name": user.get("display_name", ""),
        "role": user.get("role", "Processor"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _enqueue("users", record["id"], record)
    _ensure_flush_thread()


def mirror_activity(loan_id: int, action: str, detail: str = "", user: str = ""):
    """Queue an activity log entry."""
    if not is_enabled() or not loan_id:
        return
    record = {
        "loan_id": loan_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "detail": detail or "",
        "user": user or "",
    }
    # Activity entries are append-only; key by (loan_id, ts) so dedupe never collapses them
    key = f"{loan_id}:{record['ts']}"
    _enqueue("activity_log", key, record)
    _ensure_flush_thread()


def mirror_setting(key: str, value: Any):
    """Queue a settings entry (lender clauses, email config, etc.)."""
    if not is_enabled() or not key:
        return
    redacted = _redact(value) if isinstance(value, dict) else value
    record = {
        "key": key,
        "value_json": json.dumps(redacted),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _enqueue("settings", key, record)
    _ensure_flush_thread()


def force_flush() -> dict:
    """Manually flush the queue. Returns result dict."""
    if not is_enabled():
        return {"ok": False, "reason": "Supabase not enabled"}
    return _flush()


def restore_from_cloud() -> dict:
    """Pull all data from Supabase and overwrite local files. DESTRUCTIVE — UI must confirm."""
    if not is_enabled():
        return {"ok": False, "reason": "Supabase not enabled"}
    client = _get_client()
    if not client:
        return {"ok": False, "reason": "No client"}
    try:
        loans_res = client.table("loans").select("*").execute()
        loans = loans_res.data or []
        # Reconstruct minimal loan structure from cloud rows
        local_loans = []
        for row in loans:
            loan = {
                "id": row.get("id"),
                "loan_num": row.get("loan_num"),
                "borrower": row.get("borrower"),
                "property_address": row.get("property_address"),
                "status": row.get("status"),
                "lender": row.get("lender"),
                "loan_amount": row.get("loan_amount"),
                "purchase_price": row.get("purchase_price"),
                "loan_type": row.get("loan_type"),
                "closing_date": row.get("closing_date"),
                "loan_officer": row.get("loan_officer"),
                "loan_processor": row.get("loan_processor"),
                "contacts": json.loads(row.get("contacts_json") or "{}"),
                "documents": [],  # Documents never sync — local-only
                "conditions": [],
            }
            local_loans.append(loan)

        pipeline_path = os.path.join(os.path.dirname(__file__), "pipeline.json")
        backup_path = pipeline_path + ".pre_restore_backup"
        if os.path.exists(pipeline_path):
            try:
                import shutil
                shutil.copy2(pipeline_path, backup_path)
            except OSError:
                pass
        with open(pipeline_path, "w", encoding="utf-8") as f:
            json.dump(local_loans, f, indent=2, ensure_ascii=False)
        return {"ok": True, "restored_loans": len(local_loans),
                "backup_path": backup_path if os.path.exists(backup_path) else None}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


# ─────────────────────────── Internals ───────────────────────────
def _get_client():
    """Lazy init Supabase client. Returns None if anything fails."""
    global _client, _client_init_attempted
    if _client_init_attempted:
        return _client
    _client_init_attempted = True
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        _log_error(f"Client init failed: {e}")
        _client = None
    return _client


def _redact(obj: Any) -> Any:
    """Recursively strip sensitive keys from dicts/lists."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            kl = str(k).lower()
            if kl in _SENSITIVE_KEYS:
                continue
            # Truncate ssn_last4 if present
            if "ssn" in kl and "last4" not in kl:
                continue
            out[k] = _redact(v)
        return out
    if isinstance(obj, list):
        return [_redact(x) for x in obj]
    return obj


def _to_str(v) -> str:
    if v is None:
        return ""
    return str(v)


def _enqueue(table: str, record_id, record: dict):
    """Add to queue. Dedupe overwrites older pending writes for same key.
    Skip if hash matches last successfully sent record."""
    key = (table, str(record_id))
    h = hashlib.md5(json.dumps(record, sort_keys=True, default=str).encode()).hexdigest()
    if _record_hashes.get(key) == h:
        return  # No-op write, skip
    with _queue_lock:
        _queue[key] = record
        # Trigger immediate flush if batch is full
        if len(_queue) >= _MAX_BATCH_SIZE:
            threading.Thread(target=_flush, daemon=True).start()


def _flush() -> dict:
    """Flush the queue to Supabase. Respects hourly cap."""
    global _last_flush_ts
    client = _get_client()
    if not client:
        return {"ok": False, "reason": "No client"}

    # Hourly cap check
    now = time.time()
    with _call_log_lock:
        _call_log[:] = [t for t in _call_log if now - t < 3600]
        if len(_call_log) >= _HOURLY_CALL_CAP:
            _log_error(f"Hourly cap reached ({_HOURLY_CALL_CAP}). Flush skipped.")
            return {"ok": False, "reason": "Hourly cap reached"}

    with _queue_lock:
        if not _queue:
            return {"ok": True, "synced": 0}
        # Group by table
        by_table: dict[str, list] = {}
        keys_to_remove = []
        for key, record in _queue.items():
            table = key[0]
            by_table.setdefault(table, []).append((key, record))
            keys_to_remove.append(key)

    synced = 0
    errors = []
    for table, items in by_table.items():
        records = [r for _, r in items]
        try:
            # Ensure tables exist on first write
            _ensure_table(client, table)
            client.table(table).upsert(records).execute()
            with _call_log_lock:
                _call_log.append(time.time())
            synced += len(records)
            # Mark hashes as sent
            for key, record in items:
                h = hashlib.md5(json.dumps(record, sort_keys=True, default=str).encode()).hexdigest()
                _record_hashes[key] = h
            # Remove from queue only after successful upsert
            with _queue_lock:
                for key, _ in items:
                    _queue.pop(key, None)
        except Exception as e:
            errors.append(f"{table}: {e}")
            _log_error(f"Upsert {table} failed: {e}")

    _last_flush_ts = time.time()
    state = _load_state()
    state["last_flush"] = datetime.now(timezone.utc).isoformat()
    if errors:
        state["last_error"] = "; ".join(errors)[:500]
    else:
        state["last_error"] = None
    _save_state(state)
    return {"ok": not errors, "synced": synced, "errors": errors}


_TABLES_ENSURED = set()


def _ensure_table(client, table: str):
    """Tables are created via SQL in Supabase dashboard (see SUPABASE_SCHEMA.sql).
    This just tracks what we've tried so we don't spam logs."""
    _TABLES_ENSURED.add(table)


def _ensure_flush_thread():
    """Start the periodic flush thread if not already running."""
    global _flush_thread, _flush_thread_started
    if _flush_thread_started:
        return
    _flush_thread_started = True

    def _loop():
        while True:
            time.sleep(_FLUSH_INTERVAL_SEC)
            try:
                _flush()
            except Exception as e:
                _log_error(f"Flush loop error: {e}")

    _flush_thread = threading.Thread(target=_loop, daemon=True, name="supabase-flush")
    _flush_thread.start()


def _load_state() -> dict:
    try:
        with open(_SYNC_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _save_state(state: dict | None = None):
    try:
        if state is None:
            state = _load_state()
        state["paused"] = _paused
        with open(_SYNC_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def _log_error(msg: str):
    try:
        log = []
        if os.path.exists(_SYNC_ERROR_LOG):
            try:
                with open(_SYNC_ERROR_LOG, "r", encoding="utf-8") as f:
                    log = json.load(f) or []
            except Exception:
                log = []
        log.append({"ts": datetime.now(timezone.utc).isoformat(), "msg": msg})
        log = log[-100:]  # Keep last 100 errors
        with open(_SYNC_ERROR_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)
    except Exception:
        pass


# Load paused state at module import
try:
    _state = _load_state()
    _paused = bool(_state.get("paused", False))
except Exception:
    pass

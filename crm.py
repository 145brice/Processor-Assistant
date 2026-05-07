"""
CRM Pipeline — Processor Assistant
Manages the local loan pipeline stored in pipeline.json.
Local fallback CRM helpers using a JSON file.
"""

import json
import os
from datetime import date, datetime

_PIPELINE_FILE  = os.path.join(os.path.dirname(__file__), "pipeline.json")
_TRASH_FILE     = os.path.join(os.path.dirname(__file__), "pipeline_trash.json")  # legacy
_REMOVED_DIR    = os.path.join(os.path.dirname(__file__), "removed")
_REMOVED_CFG    = os.path.join(os.path.dirname(__file__), "removed_config.json")
_DOCS_DIR       = os.path.join(os.path.dirname(__file__), "loan_docs")
_CLOUD_LOAD_ATTEMPTED = False
_CLOUD_LOAD_OK = False

RETENTION_OPTIONS = {
    "7 days":   7,
    "14 days":  14,
    "30 days":  30,
    "60 days":  60,
    "90 days":  90,
    "Forever":  0,
}

STATUS_OPTIONS = ["Pending", "Requested", "Cleared", "Overdue", "Closed"]

# Status → CSS color class name (used in app.py)
STATUS_COLORS = {
    "Pending":   "#c0392b",   # red
    "Requested": "#e67e22",   # orange
    "Cleared":   "#27ae60",   # green
    "Overdue":   "#7f8c8d",   # gray
    "Closed":    "#2c3e50",   # dark navy
}

STATUS_EMOJI = {
    "Pending":   "●",
    "Requested": "●",
    "Cleared":   "●",
    "Overdue":   "●",
    "Closed":    "✓",
}

# Party → badge color
PARTY_COLORS = {
    "Borrower":        "#1565C0",   # blue
    "Title":           "#6A1B9A",   # purple
    "Underwriter":     "#E65100",   # orange
    "Insurance":       "#00695C",   # teal
    "Closer":          "#F9A825",   # gold
    "Jr Underwriter":  "#AD1457",   # pink
    "Manager":         "#283593",   # indigo
    "Appraiser":       "#558B2F",   # olive
}


def _load() -> list:
    """Load pipeline from durable cloud snapshot first, JSON fallback second."""
    global _CLOUD_LOAD_ATTEMPTED, _CLOUD_LOAD_OK
    if not _CLOUD_LOAD_ATTEMPTED:
        _CLOUD_LOAD_ATTEMPTED = True
        try:
            import supabase_sync
            snap = supabase_sync.load_pipeline_snapshot()
            if snap.get("ok") and isinstance(snap.get("loans"), list):
                loans = snap.get("loans") or []
                if not loans:
                    legacy = supabase_sync.load_loans_backup()
                    if legacy.get("ok") and legacy.get("loans"):
                        loans = legacy.get("loans") or []
                        supabase_sync.save_pipeline_snapshot(loans)
                _CLOUD_LOAD_OK = True
                # Cache locally for faster reads and emergency fallback.
                try:
                    with open(_PIPELINE_FILE, "w", encoding="utf-8") as f:
                        json.dump(loans, f, indent=2, ensure_ascii=False)
                except OSError:
                    pass
                return loans
            legacy = supabase_sync.load_loans_backup()
            if legacy.get("ok") and legacy.get("loans"):
                loans = legacy.get("loans") or []
                _CLOUD_LOAD_OK = True
                supabase_sync.save_pipeline_snapshot(loans)
                try:
                    with open(_PIPELINE_FILE, "w", encoding="utf-8") as f:
                        json.dump(loans, f, indent=2, ensure_ascii=False)
                except OSError:
                    pass
                return loans
        except Exception:
            pass

    if not os.path.exists(_PIPELINE_FILE):
        _sample = os.path.join(os.path.dirname(_PIPELINE_FILE), "pipeline.sample.json")
        if os.path.exists(_sample):
            try:
                import shutil
                shutil.copy2(_sample, _PIPELINE_FILE)
            except OSError:
                pass
    if not os.path.exists(_PIPELINE_FILE):
        return []
    try:
        with open(_PIPELINE_FILE, "r", encoding="utf-8") as f:
            loans = json.load(f)
        # If Supabase is configured but has no snapshot yet, seed it from the
        # current JSON file instead of letting the next deploy lose the data.
        if loans and not _CLOUD_LOAD_OK:
            try:
                import supabase_sync
                supabase_sync.save_pipeline_snapshot(loans)
            except Exception:
                pass
        return loans
    except (json.JSONDecodeError, OSError):
        return []


def _save(loans: list):
    """Save pipeline to JSON and durable Supabase snapshot when configured."""
    with open(_PIPELINE_FILE, "w", encoding="utf-8") as f:
        json.dump(loans, f, indent=2, ensure_ascii=False)
    try:
        import supabase_sync
        supabase_sync.save_pipeline_snapshot(loans)
        supabase_sync.mirror_loans_bulk(loans)
    except Exception:
        pass


def get_all_loans() -> list:
    """Return all loans in the pipeline."""
    loans = _load()
    now = datetime.now()
    changed = False
    for loan in loans:
        if loan.get("status") in ("Cleared", "Closed", "Overdue"):
            continue
        # Auto-overdue: loan has been in Requested status for 24+ hours with no response
        if loan.get("status") == "Requested" and loan.get("requested_at"):
            try:
                req_time = datetime.fromisoformat(loan["requested_at"])
                if (now - req_time).total_seconds() > 86400:
                    loan["status"] = "Overdue"
                    changed = True
            except (ValueError, TypeError):
                pass
    if changed:
        _save(loans)
    return loans


def add_loan(loan_num: str, borrower: str, status: str, due_date: str,
             missing_docs: str, folder_path: str = "",
             created_by: str = "", assigned_to: str = "",
             lock_expiry: str = "", closing_date: str = "",
             commitment_date: str = "",
             conditions: list = None, contacts: dict = None) -> dict:
    """Add a new loan to the pipeline. Returns the new loan dict."""
    loans = _load()
    new_loan = {
        "id": _next_id(loans),
        "loan_num": loan_num.strip(),
        "borrower": borrower.strip(),
        "status": status,
        "due_date": due_date,
        "closing_date": closing_date or due_date,  # fallback to due_date for compat
        "lock_expiry": lock_expiry,
        "commitment_date": commitment_date,
        "missing_docs": missing_docs.strip(),
        "folder_path": folder_path.strip(),
        "created_by": created_by,
        "assigned_to": assigned_to,
        "created": datetime.now().isoformat()[:10],
        "updated": datetime.now().isoformat()[:10],
        "notes": "",
        "conditions": conditions or [],
        "contacts": contacts or {},
    }
    loans.append(new_loan)
    _save(loans)
    return new_loan


def update_loan(loan_id: int, **kwargs):
    """Update fields on a loan by ID."""
    loans = _load()
    for loan in loans:
        if loan.get("id") == loan_id:
            # Stamp requested_at on any condition newly set to Requested
            if "conditions" in kwargs:
                existing = {c.get("text", c.get("desc", "")): c for c in loan.get("conditions", [])}
                for cond in kwargs["conditions"]:
                    key = cond.get("text", cond.get("desc", ""))
                    prev = existing.get(key, {})
                    if (cond.get("status") == "Requested"
                            and prev.get("status") != "Requested"
                            and not cond.get("requested_at")):
                        cond["requested_at"] = datetime.now().isoformat()
                    elif cond.get("status") != "Requested":
                        cond.pop("requested_at", None)
            loan.update(kwargs)
            loan["updated"] = datetime.now().isoformat()[:10]
            break
    _save(loans)


def attach_document(loan_id: int, filename: str, doc_type: str,
                    pdf_bytes: bytes | None = None,
                    extracted: dict | None = None) -> dict:
    """Record a scanned document in the loan's documents list. Returns the doc record.

    PDF bytes are NOT stored — we only keep extracted metadata. If `extracted`
    is provided, key fields are promoted to the loan record for template generation.
    """
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ").strip()
    if not safe_name:
        safe_name = f"{doc_type}.pdf"
    doc_record = {
        "filename": safe_name,
        "doc_type": doc_type,
        "attached": datetime.now().isoformat()[:16],
    }
    if extracted:
        doc_record["extracted_data"] = extracted

    promoted = _promote_fields(doc_type, extracted or {})

    loans = _load()
    for loan in loans:
        if loan.get("id") == loan_id:
            docs = loan.get("documents", [])
            docs = [d for d in docs if d.get("filename") != safe_name]
            docs.append(doc_record)
            loan["documents"] = docs
            for k, v in promoted.items():
                if v and not loan.get(k):
                    loan[k] = v
            loan["updated"] = datetime.now().isoformat()[:10]
            break
    _save(loans)
    return doc_record


def _promote_fields(doc_type: str, extracted: dict) -> dict:
    """Pick fields from extracted data that should live on the loan record."""
    out: dict = {}
    if not extracted:
        return out
    if doc_type == "Purchase Contract":
        prop = (extracted.get("property") or {}).get("address")
        price = (extracted.get("transaction") or {}).get("purchase_price")
        if prop:
            out["property_address"] = prop
        if price:
            out["purchase_price"] = price
    elif doc_type == "1003 Application":
        loan_info = extracted.get("loan") or {}
        prop = extracted.get("property_address") or loan_info.get("property_address")
        if prop:
            out["property_address"] = prop
        if loan_info.get("amount"):
            out["loan_amount"] = loan_info["amount"]
        if loan_info.get("purpose"):
            out["loan_type"] = loan_info["purpose"]
        lo = extracted.get("loan_officer") or {}
        if isinstance(lo, dict) and lo.get("name"):
            out["loan_officer"] = lo["name"]
        elif isinstance(lo, str) and lo:
            out["loan_officer"] = lo
    elif doc_type in ("Loan Estimate (LE)", "Loan Estimate"):
        # Latest LE wins on lock_expiry — processors upload new LE after re-lock.
        if extracted.get("lock_expiry"):
            out["lock_expiry"] = extracted["lock_expiry"]
        if extracted.get("loan_amount"):
            out["loan_amount"] = extracted["loan_amount"]
        if extracted.get("property_address"):
            out["property_address"] = extracted["property_address"]
        if extracted.get("purpose"):
            out["loan_type"] = extracted["purpose"]
    return out


def get_documents(loan_id: int) -> list:
    """Return the documents list for a loan."""
    loans = _load()
    for loan in loans:
        if loan.get("id") == loan_id:
            return loan.get("documents", [])
    return []


def delete_loan(loan_id: int):
    """Move a loan to the removed/ folder. Auto-expires based on retention setting."""
    loans = _load()
    removed = [l for l in loans if l.get("id") == loan_id]
    kept    = [l for l in loans if l.get("id") != loan_id]
    _save(kept)
    if removed:
        loan = removed[0]
        loan["deleted_on"] = datetime.now().isoformat()[:10]
        retention = get_retention_days()
        if retention > 0:
            from datetime import timedelta
            loan["expires_on"] = (datetime.now() + timedelta(days=retention)).isoformat()[:10]
        else:
            loan["expires_on"] = ""  # Forever
        _save_removed_loan(loan)


# ── Removed folder system ─────────────────────────────────────────────────

def _ensure_removed_dir():
    os.makedirs(_REMOVED_DIR, exist_ok=True)


def _save_removed_loan(loan: dict):
    """Save a single loan as its own JSON file in removed/."""
    _ensure_removed_dir()
    lid = loan.get("id", 0)
    path = os.path.join(_REMOVED_DIR, f"loan_{lid}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(loan, f, indent=2, ensure_ascii=False)


def get_trash() -> list:
    """Return all removed loans, auto-purging any that have expired."""
    _ensure_removed_dir()
    _auto_purge()
    # Also migrate legacy trash file if it exists
    _migrate_legacy_trash()
    items = []
    for fname in os.listdir(_REMOVED_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(_REMOVED_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                items.append(json.load(f))
        except (json.JSONDecodeError, OSError):
            continue
    items.sort(key=lambda l: l.get("deleted_on", ""), reverse=True)
    return items


def _auto_purge():
    """Delete any removed loans past their expires_on date."""
    today = date.today().isoformat()
    for fname in os.listdir(_REMOVED_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(_REMOVED_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                loan = json.load(f)
            exp = loan.get("expires_on", "")
            if exp and exp <= today:
                os.remove(path)
        except Exception:
            continue


def _migrate_legacy_trash():
    """One-time migration: move old pipeline_trash.json items into removed/ folder."""
    if not os.path.exists(_TRASH_FILE):
        return
    try:
        with open(_TRASH_FILE, "r", encoding="utf-8") as f:
            old_items = json.load(f)
        if not old_items:
            os.remove(_TRASH_FILE)
            return
        retention = get_retention_days()
        for loan in old_items:
            if "expires_on" not in loan:
                if retention > 0:
                    from datetime import timedelta
                    loan["expires_on"] = (datetime.now() + timedelta(days=retention)).isoformat()[:10]
                else:
                    loan["expires_on"] = ""
            _save_removed_loan(loan)
        os.remove(_TRASH_FILE)
    except Exception:
        pass


def restore_loan(loan_id: int):
    """Move a loan from removed/ back into the pipeline."""
    path = os.path.join(_REMOVED_DIR, f"loan_{loan_id}.json")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            loan = json.load(f)
        loan.pop("deleted_on", None)
        loan.pop("expires_on", None)
        loan["status"] = "Pending"
        loan["updated"] = datetime.now().isoformat()[:10]
        loans = _load()
        loans.append(loan)
        _save(loans)
        os.remove(path)
    except Exception:
        pass


def permanently_delete(loan_id: int):
    """Permanently remove a loan file from removed/."""
    path = os.path.join(_REMOVED_DIR, f"loan_{loan_id}.json")
    if os.path.exists(path):
        os.remove(path)


def empty_trash():
    """Permanently delete all removed loans."""
    _ensure_removed_dir()
    for fname in os.listdir(_REMOVED_DIR):
        if fname.endswith(".json"):
            os.remove(os.path.join(_REMOVED_DIR, fname))


# ── Retention config ──────────────────────────────────────────────────────

def get_retention_days() -> int:
    """Return how many days removed loans are kept. 0 = forever."""
    if not os.path.exists(_REMOVED_CFG):
        return 30  # default
    try:
        with open(_REMOVED_CFG, "r", encoding="utf-8") as f:
            return json.load(f).get("retention_days", 30)
    except Exception:
        return 30


def set_retention_days(days: int):
    """Set how many days removed loans are kept before auto-delete. 0 = forever."""
    with open(_REMOVED_CFG, "w", encoding="utf-8") as f:
        json.dump({"retention_days": days}, f, indent=2)


def set_status(loan_id: int, status: str):
    """Quick status update. Stamps requested_at when moving to Requested."""
    loans = _load()
    for loan in loans:
        if loan.get("id") == loan_id:
            if status == "Requested" and loan.get("status") != "Requested":
                loan["requested_at"] = datetime.now().isoformat()
            elif status != "Requested":
                loan.pop("requested_at", None)
            loan["status"] = status
            loan["updated"] = datetime.now().isoformat()[:10]
            break
    _save(loans)


def get_loan(loan_id: int) -> dict | None:
    """Return a single loan by ID, or None."""
    for loan in _load():
        if loan.get("id") == loan_id:
            return loan
    return None


def _next_id(loans: list) -> int:
    if not loans:
        return 1
    return max(l.get("id", 0) for l in loans) + 1


# ── Loan Activity Log ─────────────────────────────────────────────────────

_ACTIVITY_DIR = os.path.join(os.path.dirname(__file__), "loan_activity")


def log_activity(loan_id: int, action: str, detail: str = "", user: str = ""):
    """Append an activity entry for a loan. Stored per-loan in loan_activity/."""
    os.makedirs(_ACTIVITY_DIR, exist_ok=True)
    path = os.path.join(_ACTIVITY_DIR, f"loan_{loan_id}.json")
    entries = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except (json.JSONDecodeError, OSError):
            entries = []
    entries.append({
        "ts": datetime.now().isoformat()[:19],
        "action": action,
        "detail": detail,
        "user": user,
    })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    try:
        import supabase_sync
        supabase_sync.mirror_activity(loan_id, action, detail, user)
    except Exception:
        pass


def get_activity(loan_id: int) -> list:
    """Return activity log for a loan, newest first."""
    path = os.path.join(_ACTIVITY_DIR, f"loan_{loan_id}.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            entries = json.load(f)
        entries.sort(key=lambda e: e.get("ts", ""), reverse=True)
        return entries
    except (json.JSONDecodeError, OSError):
        return []

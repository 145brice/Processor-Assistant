"""
CRM Pipeline — Processor Traien
Manages the local loan pipeline stored in pipeline.json.
100% offline. No cloud. Just a local JSON file.
"""

import json
import os
from datetime import date, datetime

_PIPELINE_FILE = os.path.join(os.path.dirname(__file__), "pipeline.json")

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
    "Pending":   "🔴",
    "Requested": "🟠",
    "Cleared":   "🟢",
    "Overdue":   "⚫",
    "Closed":    "✅",
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
    """Load pipeline from JSON. Returns list of loan dicts."""
    if not os.path.exists(_PIPELINE_FILE):
        return []
    try:
        with open(_PIPELINE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(loans: list):
    """Save pipeline to JSON."""
    with open(_PIPELINE_FILE, "w", encoding="utf-8") as f:
        json.dump(loans, f, indent=2, ensure_ascii=False)


def get_all_loans() -> list:
    """Return all loans in the pipeline."""
    loans = _load()
    # Auto-flag overdue loans
    today = date.today().isoformat()
    changed = False
    for loan in loans:
        due = loan.get("due_date", "")
        if due and due < today and loan.get("status") not in ("Cleared", "Closed", "Overdue"):
            loan["status"] = "Overdue"
            changed = True
    if changed:
        _save(loans)
    return loans


def add_loan(loan_num: str, borrower: str, status: str, due_date: str,
             missing_docs: str, folder_path: str = "") -> dict:
    """Add a new loan to the pipeline. Returns the new loan dict."""
    loans = _load()
    new_loan = {
        "id": _next_id(loans),
        "loan_num": loan_num.strip(),
        "borrower": borrower.strip(),
        "status": status,
        "due_date": due_date,
        "missing_docs": missing_docs.strip(),
        "folder_path": folder_path.strip(),
        "created": datetime.now().isoformat()[:10],
        "updated": datetime.now().isoformat()[:10],
        "notes": "",
    }
    loans.append(new_loan)
    _save(loans)
    return new_loan


def update_loan(loan_id: int, **kwargs):
    """Update fields on a loan by ID."""
    loans = _load()
    for loan in loans:
        if loan.get("id") == loan_id:
            loan.update(kwargs)
            loan["updated"] = datetime.now().isoformat()[:10]
            break
    _save(loans)


def delete_loan(loan_id: int):
    """Remove a loan from the pipeline by ID."""
    loans = _load()
    loans = [l for l in loans if l.get("id") != loan_id]
    _save(loans)


def set_status(loan_id: int, status: str):
    """Quick status update."""
    update_loan(loan_id, status=status)


def _next_id(loans: list) -> int:
    if not loans:
        return 1
    return max(l.get("id", 0) for l in loans) + 1

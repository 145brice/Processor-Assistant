"""
Document Expiry Tracker - Track document expiration dates and reminders
Monitors insurance, appraisal, and other time-sensitive documents.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


DOC_EXPIRY_DAYS = {
    "insurance": 365,
    "appraisal": 120,
    "credit_report": 90,
    "title_commitment": 90,
    "voe": 30,
}


@dataclass
class ExpiringDocument:
    """Document with expiration tracking."""
    name: str
    doc_type: str
    file_path: str
    expiration_date: Optional[datetime]
    days_until_expiry: int
    is_expired: bool
    reminder_sent: bool


def parse_expiry_from_filename(filename: str) -> Optional[datetime]:
    """Try to parse expiration date from filename."""
    patterns = [
        (r'(\d{4})[-_](\d{2})[-_](\d{2})', "%Y-%m-%d"),
        (r'(\d{2})[-_](\d{2})[-_](\d{4})', "%m-%d-%Y"),
        (r'exp[iry]?[-_]?(\d{4})[-_](\d{2})[-_](\d{2})', "%Y-%m-%d"),
    ]
    
    for pattern, fmt in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            try:
                date_str = match.group(0).replace("_", "-")
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
    
    return None


def get_default_expiry_days(doc_type: str) -> int:
    """Get default expiry days for document type."""
    doc_type_lower = doc_type.lower()
    
    for key, days in DOC_EXPIRY_DAYS.items():
        if key in doc_type_lower:
            return days
    
    return 90


def calculate_expiry_date(
    file_path: Path,
    doc_type: str = None,
    custom_days: int = None
) -> datetime:
    """
    Calculate expiration date for document.
    First checks filename, then uses mtime + default.
    """
    parsed = parse_expiry_from_filename(file_path.name)
    if parsed:
        return parsed
    
    if custom_days:
        days = custom_days
    else:
        days = get_default_expiry_days(doc_type) if doc_type else 90
    
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    return mtime + timedelta(days=days)


def check_document_expiry(
    file_path: Path,
    doc_type: str,
    warn_days: list = None
) -> ExpiringDocument:
    """Check single document for expiry status."""
    if warn_days is None:
        warn_days = [30, 60, 90]
    
    expiration = calculate_expiry_date(file_path, doc_type)
    today = datetime.now()
    days_until = (expiration - today).days
    is_expired = days_until < 0
    
    reminder = any(days_until <= w for w in warn_days)
    
    return ExpiringDocument(
        name=file_path.name,
        doc_type=doc_type,
        file_path=str(file_path),
        expiration_date=expiration,
        days_until_expiry=days_until,
        is_expired=is_expired,
        reminder_sent=False,
    )


def scan_loan_folder_for_expiry(loan_folder: Path) -> list:
    """Scan loan folder for expiring documents."""
    results = []
    
    if not loan_folder.exists():
        return results
    
    doc_type_map = {
        "insurance": ["insurance", "hoi", "hazard", "policy"],
        "appraisal": ["appraisal", " appraisal", "1004", "1075"],
        "credit_report": ["credit", "tri-merge"],
        "title": ["title", "commitment", "prelim"],
        "voe": ["voe", "verification of employment"],
    }
    
    for file in loan_folder.rglob("*"):
        if not file.is_file() or file.name.startswith("."):
            continue
        
        filename_lower = file.name.lower()
        
        for doc_type, keywords in doc_type_map.items():
            if any(kw in filename_lower for kw in keywords):
                exp_doc = check_document_expiry(file, doc_type)
                results.append(exp_doc)
                break
    
    return results


def get_expiry_warnings(loan_folder: Path) -> dict:
    """Get all expiry warnings for loan folder."""
    docs = scan_loan_folder_for_expiry(loan_folder)
    
    expired = []
    expiring_soon = []
    okay = []
    
    for doc in docs:
        if doc.is_expired:
            expired.append(doc)
        elif doc.days_until_expiry <= 30:
            expiring_soon.append(doc)
        else:
            okay.append(doc)
    
    return {
        "expired": expired,
        "expiring_soon": expiring_soon,
        "okay": okay,
        "has_warnings": bool(expired or expiring_soon),
    }


def get_reminder_email_body(loan_folder: Path) -> str:
    """Generate reminder email for expiring documents."""
    warnings = get_expiry_warnings(loan_folder)
    
    body = "The following documents need attention:\n\n"
    
    if warnings["expired"]:
        body += "EXPIRED:\n"
        for doc in warnings["expired"]:
            body += f"  - {doc.name}\n"
        body += "\n"
    
    if warnings["expiring_soon"]:
        body += "Expiring Soon:\n"
        for doc in warnings["expiring_soon"]:
            days = doc.days_until_expiry
            body += f"  - {doc.name} (expires in {days} days)\n"
        body += "\n"
    
    body += "Please provide updated documents."
    
    return body


EXPIRY_DB_PATH = Path.home() / "Desktop" / "MortgageHub" / "expiry_db.json"


def load_expiry_db() -> dict:
    """Load expiry tracking database."""
    if EXPIRY_DB_PATH.exists():
        with open(EXPIRY_DB_PATH) as f:
            return json.load(f)
    return {}


def save_expiry_db(db: dict) -> None:
    """Save expiry tracking database."""
    EXPIRY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EXPIRY_DB_PATH, "w") as f:
        json.dump(db, f, indent=2)


def track_document(
    loan_id: str,
    doc_type: str,
    file_path: str,
    expiration_date: datetime = None
) -> None:
    """Track a document's expiration in database."""
    db = load_expiry_db()
    
    if loan_id not in db:
        db[loan_id] = {}
    
    key = f"{doc_type}_{Path(file_path).name}"
    
    if expiration_date:
        exp_date = expiration_date.isoformat()
    else:
        exp_date = calculate_expiry_date(Path(file_path), doc_type).isoformat()
    
    db[loan_id][key] = {
        "doc_type": doc_type,
        "file_path": file_path,
        "expiration_date": exp_date,
        "tracked_at": datetime.now().isoformat(),
    }
    
    save_expiry_db(db)


def get_tracked_documents(loan_id: str) -> list:
    """Get all tracked documents for a loan."""
    db = load_expiry_db()
    
    if loan_id not in db:
        return []
    
    results = []
    today = datetime.now()
    
    for key, info in db[loan_id].items():
        exp_date = datetime.fromisoformat(info["expiration_date"])
        days_until = (exp_date - today).days
        
        results.append({
            "name": key,
            "doc_type": info["doc_type"],
            "file_path": info["file_path"],
            "expiration_date": exp_date.isoformat(),
            "days_until_expiry": days_until,
            "is_expired": days_until < 0,
        })
    
    return sorted(results, key=lambda x: x["days_until_expiry"])


def get_all_expiring() -> list:
    """Get all documents expiring within 30 days across all loans."""
    db = load_expiry_db()
    results = []
    today = datetime.now()
    
    for loan_id, docs in db.items():
        for key, info in docs.items():
            exp_date = datetime.fromisoformat(info["expiration_date"])
            days_until = (exp_date - today).days
            
            if days_until <= 30:
                results.append({
                    "loan_id": loan_id,
                    "name": key,
                    "doc_type": info["doc_type"],
                    "expiration_date": exp_date.isoformat(),
                    "days_until_expiry": days_until,
                    "is_expired": days_until < 0,
                })
    
    return sorted(results, key=lambda x: x["days_until_expiry"])


def clear_expired_from_db() -> int:
    """Remove expired documents from tracking. Returns count removed."""
    db = load_expiry_db()
    today = datetime.now()
    removed = 0
    
    for loan_id in list(db.keys()):
        for key in list(db[loan_id].keys()):
            exp_date = datetime.fromisoformat(db[loan_id][key]["expiration_date"])
            if exp_date < today - timedelta(days=90):
                del db[loan_id][key]
                removed += 1
        
        if not db[loan_id]:
            del db[loan_id]
    
    if removed > 0:
        save_expiry_db(db)
    
    return removed
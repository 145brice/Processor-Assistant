"""
Loan Snapshot - Complete vs Missing document view
Provides a comprehensive snapshot of loan document status.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


DOCUMENT_REQUIREMENTS = {
    "1003 Application": {
        "required": True,
        "aliases": ["1003", "uniform residential loan application", "urla"],
    },
    "Credit Report": {
        "required": True,
        "aliases": ["credit", "credit report", "tri-merge", "credit pull"],
    },
    "Purchase Contract": {
        "required": True,
        "aliases": ["purchase contract", "agreement", "sales contract", "contract"],
    },
    "Bank Statement": {
        "required": True,
        "aliases": ["bank statement", "bank stmt", "checking", "savings"],
    },
    "Pay Stub": {
        "required": True,
        "aliases": ["pay stub", "paystub", "pay advice", "earnings"],
    },
    "W-2": {
        "required": True,
        "aliases": ["w-2", "w2", "wage statement"],
    },
    "Tax Return": {
        "required": True,
        "aliases": ["tax return", "1040", "tax transcript"],
    },
    "Appraisal": {
        "required": True,
        "aliases": ["appraisal", "property valuation", "1004", "1075"],
    },
    "Title Commitment": {
        "required": True,
        "aliases": ["title", "preliminary title", "title commitment"],
    },
    "Hazard Insurance": {
        "required": True,
        "aliases": ["insurance", "hazard insurance", "hoi", "homeowner"],
    },
    "Closing Disclosure": {
        "required": True,
        "aliases": ["cd", "closing disclosure", "cd signed"],
    },
    "Loan Estimate": {
        "required": False,
        "aliases": ["le", "loan estimate"],
    },
    "Gift Letter": {
        "required": False,
        "aliases": ["gift letter", "gift funds", "donor"],
    },
    "VOE": {
        "required": False,
        "aliases": ["voe", "verification of employment", "employment verification"],
    },
}


def scan_folder_for_documents(folder_path: Path) -> dict:
    """
    Scan a loan folder for documents.
    Returns dict of document types found and their paths.
    """
    found = {}
    
    if not folder_path.exists():
        return found
    
    for file in folder_path.rglob("*"):
        if not file.is_file() or file.name.startswith("."):
            continue
        
        filename_lower = file.name.lower()
        
        for doc_type, info in DOCUMENT_REQUIREMENTS.items():
            for alias in info.get("aliases", []):
                if alias in filename_lower:
                    if doc_type not in found:
                        found[doc_type] = []
                    
                    found[doc_type].append({
                        "file": file.name,
                        "path": str(file),
                        "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
                    })
                    break
    
    return found


def get_document_age_days(file_path: Path) -> int:
    """Get age of document in days."""
    if not file_path.exists():
        return None
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    return (datetime.now() - mtime).days


def is_document_stale(file_path: Path, threshold: int = 90) -> bool:
    """Check if document is older than threshold days."""
    age = get_document_age_days(file_path)
    if age is None:
        return False
    return age > threshold


def generate_snapshot(loan_folder: Path, include_stale_check: bool = True) -> dict:
    """
    Generate a complete snapshot of loan documents.
    Returns complete vs missing view.
    """
    found_docs = scan_folder_for_documents(loan_folder)
    
    complete = []
    missing = []
    stale = []
    partial = []
    
    for doc_type, info in DOCUMENT_REQUIREMENTS.items():
        required = info.get("required", False)
        files = found_docs.get(doc_type, [])
        
        if files:
            for f in files:
                file_path = Path(f["path"])
                age_days = get_document_age_days(file_path)
                
                if include_stale_check and age_days and age_days > 30:
                    stale.append({
                        "document": doc_type,
                        "file": f["file"],
                        "age_days": age_days,
                        "path": f["path"],
                    })
                else:
                    complete.append({
                        "document": doc_type,
                        "file": f["file"],
                        "age_days": age_days,
                        "path": f["path"],
                    })
        else:
            if required:
                missing.append({
                    "document": doc_type,
                    "required": required,
                })
            else:
                partial.append({
                    "document": doc_type,
                    "required": required,
                })
    
    summary = {
        "complete_count": len(complete),
        "missing_count": len(missing),
        "partial_count": len(partial),
        "stale_count": len(stale),
        "total_required": sum(1 for d in DOCUMENT_REQUIREMENTS.values() if d.get("required")),
    }
    
    complete_pct = 0
    if summary["total_required"] > 0:
        complete_pct = (len(complete) / summary["total_required"]) * 100
    
    if missing:
        status = f"Missing {len(missing)} required"
    elif stale:
        status = "Documents need refresh"
    else:
        status = "Complete" if complete_pct >= 100 else f"{complete_pct:.0f}% Complete"
    
    return {
        "loan_folder": str(loan_folder),
        "generated_at": datetime.now().isoformat(),
        "status": status,
        "complete_pct": complete_pct,
        "summary": summary,
        "complete": complete,
        "missing": missing,
        "partial": partial,
        "stale": stale,
    }


def get_age_warnings(snapshot: dict, thresholds: list = None) -> list:
    """Get age warnings for documents."""
    if thresholds is None:
        thresholds = [30, 60, 90]
    
    warnings = []
    
    for doc in snapshot.get("complete", []):
        age = doc.get("age_days")
        if age:
            for threshold in thresholds:
                if age > threshold:
                    warnings.append({
                        "document": doc["document"],
                        "file": doc["file"],
                        "age_days": age,
                        "threshold": threshold,
                        "warning": f"Over {threshold} days old",
                    })
    
    return warnings


def compare_to_conditions(snapshot: dict, conditions: list) -> dict:
    """
    Compare snapshot to actual conditions list.
    Flags documents that are needed per conditions but not in folder.
    """
    missing_per_conditions = []
    
    for cond in conditions:
        cond_lower = cond.lower()
        found = False
        
        for doc_type in snapshot.get("complete", []):
            if doc_type.get("document", "").lower() in cond_lower:
                found = True
                break
        
        if not found:
            missing_per_conditions.append(cond)
    
    return {
        "conditions": conditions,
        "missing_per_conditions": missing_per_conditions,
    }


def get_missing_docs_email_body(snapshot: dict, include_optional: bool = False) -> str:
    """Generate email body for missing documents."""
    missing = snapshot.get("missing", [])
    
    if include_optional:
        missing = missing + snapshot.get("partial", [])
    
    if not missing:
        return "All required documents have been received. Thank you!"
    
    body = "The following items are needed to complete your loan file:\n\n"
    
    for i, doc in enumerate(missing, 1):
        body += f"{i}. {doc['document']}\n"
    
    body += "\nPlease provide these documents at your earliest convenience."
    
    return body


def save_snapshot(snapshot: dict, folder: Path = None) -> Path:
    """Save snapshot to JSON file."""
    if folder is None:
        folder = Path.home() / "Desktop" / "MortgageHub" / "snapshots"
    
    folder.mkdir(parents=True, exist_ok=True)
    
    loan_name = Path(snapshot["loan_folder"]).name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    file_path = folder / f"snapshot_{loan_name}_{timestamp}.json"
    
    with open(file_path, "w") as f:
        json.dump(snapshot, f, indent=2)
    
    return file_path


def load_snapshot(file_path: Path) -> dict:
    """Load snapshot from JSON file."""
    with open(file_path) as f:
        return json.load(f)


def get_latest_snapshot(loan_name: str) -> Optional[dict]:
    """Get most recent snapshot for a loan."""
    folder = Path.home() / "Desktop" / "MortgageHub" / "snapshots"
    
    if not folder.exists():
        return None
    
    snapshots = sorted(
        folder.glob(f"snapshot_{loan_name}_*.json"),
        reverse=True
    )
    
    if snapshots:
        return load_snapshot(snapshots[0])
    
    return None
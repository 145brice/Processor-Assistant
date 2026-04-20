"""
Feedback Reporter - Report Issue with automatic SSN/bank account masking
Masks sensitive data to last 4 digits before sharing.
"""

import re
import os
import json
from datetime import datetime
from pathlib import Path
import io

try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


REPORT_FOLDER = Path.home() / "Desktop" / "MortgageHub" / "Feedback_Reports"


def mask_ssn(text: str) -> str:
    """Mask SSN to XXX-XX-XXXX."""
    return re.sub(r'\b(\d{3})[-]?(\d{2})[-]?(\d{4})\b', r'XXX-XX-\3', text)


def mask_bank_account(text: str) -> str:
    """Mask bank account to XXXX-XXXX-XXXX last 4."""
    return re.sub(r'\b(\d{4,9})(\d{4})\b', r'****\2', text)


def mask_dob(text: str) -> str:
    """Mask DOB."""
    return re.sub(r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b', r'XX/XX/XXXX', text)


def mask_all_sensitive(text: str) -> str:
    """Apply all masking patterns."""
    text = mask_ssn(text)
    text = mask_bank_account(text)
    text = mask_dob(text)
    return text


def _redact_pdf_page(page) -> None:
    """Redact sensitive data on a fitz page in-place."""
    text = page.get_text()
    masked = mask_all_sensitive(text)
    
    if masked != text:
        for rect in page.search_for("XXX-XX"):
            page.add_redact_annot(rect, fill=True)
        for rect in page.search_for("XXXX"):
            page.add_redact_annot(rect, fill=True)
        page.apply_redactions()


def redact_pdf_file(src_path: str, dst_path: str) -> bool:
    """Create redacted copy of PDF. Returns success."""
    if not HAS_PYMUPDF:
        return False
    
    try:
        doc = fitz.open(src_path)
        for page in doc:
            _redact_pdf_page(page)
        doc.save(dst_path)
        doc.close()
        return True
    except Exception:
        return False


def _extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF for condition analysis."""
    if HAS_PYPDF:
        try:
            reader = PdfReader(pdf_path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text
        except Exception:
            pass
    return ""


def save_report(user_notes: str, attached_file: str = None, loan_id: str = None) -> dict:
    """
    Save a feedback report with optional attached document.
    Replaces sensitive data in PDF before saving.
    """
    REPORT_FOLDER.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_folder = REPORT_FOLDER / f"Report_{timestamp}"
    report_folder.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "timestamp": timestamp,
        "loan_id": loan_id,
        "notes": user_notes,
    }
    
    with open(report_folder / "notes.txt", "w", encoding="utf-8") as f:
        f.write(f"Date: {datetime.now().isoformat()}\n")
        if loan_id:
            f.write(f"Loan ID: {loan_id}\n")
        f.write(f"\nIssue Description:\n{user_notes}\n")
    
    with open(report_folder / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    result = {
        "success": True,
        "report_path": str(report_folder),
        "report_id": timestamp,
    }
    
    if attached_file and Path(attached_file).exists():
        src = Path(attached_file)
        
        pdf_text = _extract_text_from_pdf(str(src))
        masked_text = mask_all_sensitive(pdf_text)
        
        with open(report_folder / "document_text.txt", "w", encoding="utf-8") as f:
            f.write(masked_text)
        
        if src.suffix.lower() == ".pdf":
            dst_pdf = report_folder / "PROBLEM_DOCUMENT.pdf"
            if redact_pdf_file(str(src), str(dst_pdf)):
                result["redacted_file"] = str(dst_pdf)
            else:
                result["redacted_file"] = None
        else:
            import shutil
            dst = report_folder / src.name
            shutil.copy2(src, dst)
            result["attached_file"] = str(dst)
    
    return result


def get_all_reports() -> list:
    """List all feedback reports, newest first."""
    if not REPORT_FOLDER.exists():
        return []
    
    reports = []
    for folder in sorted(REPORT_FOLDER.iterdir(), reverse=True):
        if not folder.is_dir() or not folder.name.startswith("Report_"):
            continue
        
        meta_file = folder / "metadata.json"
        meta = {}
        if meta_file.exists():
            try:
                with open(meta_file) as f:
                    meta = json.load(f)
            except Exception:
                pass
        
        files = [f.name for f in folder.iterdir() if f.is_file()]
        
        reports.append({
            "folder": str(folder),
            "timestamp": meta.get("timestamp", folder.name.replace("Report_", "")),
            "loan_id": meta.get("loan_id"),
            "notes": meta.get("notes", "")[:100],
            "files": files,
        })
    
    return reports


def get_report(report_id: str) -> dict:
    """Get specific report by ID."""
    report_folder = REPORT_FOLDER / f"Report_{report_id}"
    if not report_folder.exists():
        return None
    
    notes_file = report_folder / "notes.txt"
    notes = ""
    if notes_file.exists():
        notes = notes_file.read_text(encoding="utf-8")
    
    files = {}
    for f in report_folder.iterdir():
        if f.is_file():
            files[f.name] = str(f)
    
    return {
        "report_path": str(report_folder),
        "notes": notes,
        "files": files,
    }
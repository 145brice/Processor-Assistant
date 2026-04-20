"""
Folder Manager - Smart folder creation for Mortgage Processor
- Auto-creates Conditions_N folders only when approval with conditions detected
- Fetch feature: scan folders for matching documents
- Clean logic: max 7 Conditions folders, merge similar ones
- Always logs folder operations
"""

import os
import json
from datetime import datetime
from pathlib import Path

# Base directory for all mortgage files
BASE_DIR = Path.home() / "Desktop" / "MortgageHub"

# Folder structure
FOLDERS = {
    "clients_active": BASE_DIR / "Clients" / "Active",
    "clients_closed": BASE_DIR / "Clients" / "Closed",
    "clients_dead": BASE_DIR / "Clients" / "Dead",
    "uploads": BASE_DIR / "Uploads",
}

# Condition keywords for matching documents to conditions
CONDITION_KEYWORDS = {
    "VOE": ["voe", "verification of employment", "employment verification"],
    "pay_stub": ["pay stub", "paystub", "pay advice", "earnings statement"],
    "bank_statement": ["bank statement", "checking account", "savings account"],
    "tax_return": ["tax return", "1040", "schedule c", "w-2"],
    "appraisal": ["appraisal", "property valuation", "1004"],
    "title": ["title commitment", "preliminary title", "title report"],
    "insurance": ["insurance binder", "hazard insurance", "homeowner insurance"],
    "gift_letter": ["gift letter", "gift funds", "donor letter"],
    "approval_letter": ["approval letter", "commitment letter", "clear to close"],
    "closing_disclosure": ["closing disclosure", "CD", "settlement statement"],
    "loan_estimate": ["loan estimate", "LE"],
}

# Log file
LOG_FILE = BASE_DIR / "folder_operations.log"


def ensure_base_structure():
    """Create base folder structure on first run."""
    created = []
    for key, path in FOLDERS.items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
    
    # Create test client if Active is empty
    active_dir = FOLDERS["clients_active"]
    if not any(active_dir.iterdir()):
        test_client = active_dir / "Test_Doe"
        (test_client / "Submission").mkdir(parents=True, exist_ok=True)
        (test_client / "Closing_Package").mkdir(parents=True, exist_ok=True)
        created.append(f"{test_client}/Submission")
        created.append(f"{test_client}/Closing_Package")
    
    return created


def get_client_folder(client_name: str, status: str = "active") -> Path:
    """Get or create client folder."""
    status_map = {"active": "clients_active", "closed": "clients_closed", "dead": "clients_dead"}
    base = FOLDERS.get(status_map.get(status, "clients_active"), FOLDERS["clients_active"])
    client_dir = base / client_name
    if not client_dir.exists():
        client_dir.mkdir(parents=True, exist_ok=True)
        log_operation("CREATE", str(client_dir), f"New client folder ({status})")
    return client_dir


def get_next_conditions_number(client_dir: Path) -> int:
    """Get next Conditions_N number for a client."""
    existing = sorted([d for d in client_dir.iterdir() if d.is_dir() and d.name.startswith("Conditions_")])
    if not existing:
        return 1
    # Extract numbers and get max
    nums = []
    for d in existing:
        try:
            num = int(d.name.split("_")[1])
            nums.append(num)
        except (IndexError, ValueError):
            continue
    return max(nums) + 1 if nums else 1


def get_conditions_count(client_dir: Path) -> int:
    """Count existing Conditions folders."""
    return len([d for d in client_dir.iterdir() if d.is_dir() and d.name.startswith("Conditions_")])


def create_conditions_folder(client_dir: Path, condition_desc: str = "") -> Path:
    """
    Create next Conditions_N folder.
    Max 7 - if exceeded, merge into last one.
    """
    count = get_conditions_count(client_dir)
    
    if count >= 7:
        # Merge into last Conditions folder
        existing = sorted([d for d in client_dir.iterdir() if d.is_dir() and d.name.startswith("Conditions_")])
        last_folder = existing[-1] if existing else client_dir / "Conditions_7"
        log_operation("MERGE", str(last_folder), f"Max 7 Conditions reached - merging into {last_folder.name}")
        return last_folder
    
    next_num = get_next_conditions_number(client_dir)
    new_folder = client_dir / f"Conditions_{next_num}"
    new_folder.mkdir(parents=True, exist_ok=True)
    
    log_operation("CREATE", str(new_folder), f"Auto-created for: {condition_desc or 'condition'}")
    return new_folder


def match_condition_to_folder(condition_text: str, client_dir: Path) -> tuple[Path, bool]:
    """
    Match a condition to existing Conditions_N folder.
    Returns (folder_path, is_new_folder).
    """
    condition_lower = condition_text.lower()
    
    # Check existing Conditions folders for keyword match
    existing = sorted([d for d in client_dir.iterdir() if d.is_dir() and d.name.startswith("Conditions_")])
    
    for folder in existing:
        # Check if there's a metadata file with condition description
        meta_file = folder / ".condition_meta.json"
        if meta_file.exists():
            try:
                with open(meta_file) as f:
                    meta = json.load(f)
                    meta_desc = meta.get("description", "").lower()
                    # Simple keyword overlap check
                    if any(kw in meta_desc for kw in condition_lower.split() if len(kw) > 3):
                        return folder, False
            except (json.JSONDecodeError, IOError):
                pass
        
        # Fallback: check folder number (first conditions go to first folders)
        # This is simplistic - real matching would use embeddings or better NLP
    
    # No match - create new folder
    new_folder = create_conditions_folder(client_dir, condition_text[:50])
    
    # Save metadata
    meta_file = new_folder / ".condition_meta.json"
    with open(meta_file, "w") as f:
        json.dump({
            "description": condition_text,
            "created": datetime.now().isoformat(),
        }, f)
    
    return new_folder, True


def log_operation(operation: str, path: str, details: str = ""):
    """Log folder operation to log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {operation}: {path}"
    if details:
        log_entry += f" - {details}"
    log_entry += "\n"
    
    try:
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    except IOError:
        pass  # Don't crash if can't log


def scan_for_documents(client_dir: Path, search_terms: list[str]) -> list[dict]:
    """
    Scan client folders for documents matching search terms.
    Returns list of {file, path, folder, match_score, is_old}.
    """
    results = []
    scan_folders = [
        client_dir / "Submission",
        client_dir / "Closing_Package",
        *[d for d in client_dir.iterdir() if d.is_dir() and d.name.startswith("Conditions_")],
    ]
    
    for folder in scan_folders:
        if not folder.exists():
            continue
        for file in folder.iterdir():
            if not file.is_file() or file.name.startswith("."):
                continue
            
            file_lower = file.name.lower()
            match_count = sum(1 for term in search_terms if term.lower() in file_lower)
            
            if match_count > 0:
                # Check if it's an old version (by date in filename or modified time)
                is_old = _check_if_old_version(file)
                
                results.append({
                    "file": file.name,
                    "path": str(file),
                    "folder": folder.name,
                    "match_score": match_count / len(search_terms),
                    "is_old": is_old,
                })
    
    # Sort by match score descending
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results


def _check_if_old_version(file: Path) -> bool:
    """Check if file appears to be an old version (>30 days old)."""
    import re

    # Try to parse date from filename
    date_patterns = [
        (r'(\d{4})[-_](\d{2})[-_](\d{2})', "%Y-%m-%d"),   # 2025-01-15
        (r'(\d{2})[-_](\d{2})[-_](\d{4})', "%m-%d-%Y"),    # 01-15-2025
        (r'(\d{8})', "%Y%m%d"),                              # 20250115
    ]

    for pattern, fmt in date_patterns:
        match = re.search(pattern, file.name)
        if match:
            try:
                date_str = match.group(0).replace("_", "-")
                file_date = datetime.strptime(date_str, fmt)
                return (datetime.now() - file_date).days > 30
            except ValueError:
                continue

    # Fallback: check file modified time
    try:
        mtime = datetime.fromtimestamp(file.stat().st_mtime)
        return (datetime.now() - mtime).days > 30
    except (OSError, ValueError):
        return False


def fetch_for_condition(client_dir: Path, condition_num: int) -> list[dict]:
    """
    Fetch documents matching a specific Conditions_N folder.
    Returns list of found documents with actions.
    """
    # Get condition description from metadata
    conditions_folder = client_dir / f"Conditions_{condition_num}"
    if not conditions_folder.exists():
        return []
    
    meta_file = conditions_folder / ".condition_meta.json"
    search_terms = []
    
    if meta_file.exists():
        try:
            with open(meta_file) as f:
                meta = json.load(f)
                desc = meta.get("description", "")
                # Extract keywords from description
                search_terms = [w for w in desc.split() if len(w) > 3 and w.lower() not in {"the", "and", "for", "with", "from", "need", "needed", "required"}]
        except (json.JSONDecodeError, IOError):
            pass
    
    # Fallback: use condition keywords
    if not search_terms:
        for key, terms in CONDITION_KEYWORDS.items():
            if key.lower() in conditions_folder.name.lower():
                search_terms = terms[:3]
                break
    
    if not search_terms:
        search_terms = ["document", "file"]  # Last resort
    
    return scan_for_documents(client_dir, search_terms)


def move_file(src: Path, dst_folder: Path, make_copy: bool = False) -> dict:
    """Move or copy file to destination folder."""
    import shutil
    
    dst = dst_folder / src.name
    
    # Handle duplicate names
    counter = 1
    while dst.exists():
        stem = src.stem
        suffix = src.suffix
        dst = dst_folder / f"{stem}_{counter}{suffix}"
        counter += 1
    
    try:
        if make_copy:
            shutil.copy2(src, dst)
            action = "COPY"
        else:
            shutil.move(str(src), str(dst))
            action = "MOVE"
        
        log_operation(action, str(dst), f"From: {src.parent.name}")
        return {"success": True, "action": action, "path": str(dst)}
    except (IOError, shutil.Error) as e:
        return {"success": False, "error": str(e)}


def create_folder_manual(client_dir: Path, folder_name: str) -> dict:
    """Manually create a folder (user-initiated)."""
    new_folder = client_dir / folder_name
    if new_folder.exists():
        return {"success": False, "error": "Folder already exists"}
    
    new_folder.mkdir(parents=True, exist_ok=True)
    log_operation("CREATE_MANUAL", str(new_folder), "User-created")
    return {"success": True, "path": str(new_folder)}


def get_folder_structure(client_dir: Path) -> list[dict]:
    """Get current folder structure for a client."""
    structure = []

    for item in sorted(client_dir.iterdir()):
        if not item.is_dir() or item.name.startswith("."):
            continue

        file_count = len([f for f in item.iterdir() if f.is_file() and not f.name.startswith(".")])

        structure.append({
            "name": item.name,
            "path": str(item),
            "file_count": file_count,
            "is_conditions": item.name.startswith("Conditions_"),
        })

    return structure


# Maps doc type to the subfolder it belongs in
DOC_TYPE_FOLDER_MAP = {
    "Approval Letter":          "Approval",
    "Closing Disclosure (CD)":  "Closing_Package",
    "Loan Estimate (LE)":       "Closing_Package",
    "Change of Circumstance (COC)": "Closing_Package",
    "Broker Package (BP)":      "Submission",
    "Credit Report":            "Submission",
    "1003 Application":         "Submission",
    "W-2":                      "Income",
    "Tax Return":               "Income",
    "Pay Stub":                 "Income",
    "Bank Statement":           "Assets",
    "Gift Letter":              "Assets",
    "Social Security Card":     "Submission",
    "Driver License":           "Submission",
}


def suggest_save_folder(client_dir: Path, doc_type: str) -> Path:
    """Return the best subfolder for this doc type, creating it if needed."""
    subfolder_name = DOC_TYPE_FOLDER_MAP.get(doc_type, "Misc")
    subfolder = client_dir / subfolder_name
    subfolder.mkdir(parents=True, exist_ok=True)
    return subfolder


def check_duplicate(folder: Path, filename: str) -> dict:
    """
    Check if a file with the same or similar name already exists in the folder.
    Returns {duplicate: bool, existing: list of matching filenames}.
    """
    if not folder.exists():
        return {"duplicate": False, "existing": []}

    stem = Path(filename).stem.lower()
    existing = []
    for f in folder.iterdir():
        if f.is_file() and not f.name.startswith("."):
            # Exact name match
            if f.name.lower() == filename.lower():
                existing.append({"name": f.name, "match": "exact"})
            # Similar stem (e.g. "PNC 2728 - 2-24" vs "PNC 2728 - 2-24 (1)")
            elif stem in f.stem.lower() or f.stem.lower() in stem:
                existing.append({"name": f.name, "match": "similar"})

    return {"duplicate": len(existing) > 0, "existing": existing}


def save_file_to_folder(pdf_bytes: bytes, filename: str, folder: Path) -> dict:
    """Write pdf_bytes to folder/filename. Renames if exact duplicate exists."""
    import hashlib

    folder.mkdir(parents=True, exist_ok=True)
    dst = folder / filename

    # If exact file already there and identical content, skip
    if dst.exists():
        existing_hash = hashlib.md5(dst.read_bytes()).hexdigest()
        new_hash = hashlib.md5(pdf_bytes).hexdigest()
        if existing_hash == new_hash:
            return {"success": True, "path": str(dst), "action": "skipped_identical"}
        # Different content — rename with counter
        counter = 1
        while dst.exists():
            dst = folder / f"{Path(filename).stem}_{counter}{Path(filename).suffix}"
            counter += 1

    try:
        dst.write_bytes(pdf_bytes)
        log_operation("SAVE", str(dst), f"Doc type saved to {folder.name}")
        return {"success": True, "path": str(dst), "action": "saved"}
    except IOError as e:
        return {"success": False, "error": str(e)}


def delete_folder(folder: Path) -> dict:
    """Delete a folder and all its contents. Logs the operation."""
    import shutil

    if not folder.exists():
        return {"success": False, "error": "Folder does not exist"}
    try:
        file_count = sum(1 for f in folder.rglob("*") if f.is_file())
        shutil.rmtree(folder)
        log_operation("DELETE", str(folder), f"Removed {file_count} file(s)")
        return {"success": True, "files_removed": file_count}
    except (IOError, OSError) as e:
        return {"success": False, "error": str(e)}


def find_matching_clients(name_hint: str) -> list[dict]:
    """
    Search all client folders (Active/Closed/Dead) for names similar to name_hint.
    name_hint can be "John Smith", "SMITH JOHN", "Smith_John", etc.
    Returns list of {name, path, status, score} sorted best-match first.
    """
    import re

    if not name_hint or len(name_hint.strip()) < 2:
        return []

    # Normalize hint into individual tokens
    hint_tokens = set(
        t.lower() for t in re.split(r'[\s_,\-]+', name_hint.strip()) if len(t) > 1
    )

    results = []
    for status_key, base_path in [
        ("active", FOLDERS["clients_active"]),
        ("closed", FOLDERS["clients_closed"]),
        ("dead",   FOLDERS["clients_dead"]),
    ]:
        if not base_path.exists():
            continue
        for folder in base_path.iterdir():
            if not folder.is_dir():
                continue
            folder_tokens = set(
                t.lower() for t in re.split(r'[\s_,\-]+', folder.name) if len(t) > 1
            )
            overlap = hint_tokens & folder_tokens
            if overlap:
                score = len(overlap) / max(len(hint_tokens), len(folder_tokens))
                results.append({
                    "name": folder.name,
                    "path": folder,
                    "status": status_key,
                    "score": score,
                })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]


def clean_filename(filename: str, doc_type: str = None) -> str:
    """
    Clean and normalize filename for storage.
    Removes special chars, fixes spacing, applies smart naming.
    """
    import re
    
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    
    stem = stem.strip()
    stem = re.sub(r'[\s\-_]+', ' ', stem)
    stem = re.sub(r'[^\w\s\-\(\)\.]', '', stem)
    stem = re.sub(r'\s+', '_', stem)
    stem = stem.strip('_')
    
    if doc_type:
        type_prefixes = {
            "pay_stub": "Paystub",
            "bank_statement": "BankStmt",
            "tax_return": "TaxReturn",
            "w-2": "W2",
            "appraisal": "Appraisal",
            "title": "Title",
            "insurance": "HOI",
            "1003": "1003",
            "credit_report": "Credit",
            "approval_letter": "Approval",
            "closing_disclosure": "CD",
            "loan_estimate": "LE",
            "gift_letter": "GiftLetter",
        }
        prefix = type_prefixes.get(doc_type.lower(), doc_type)
        
        if not any(prefix.lower() in stem.lower() for _ in [1]):
            stem = f"{prefix}_{stem}"
    
    return stem + suffix.lower()


def smart_rename(file_path: Path, doc_type: str = None, loan_name: str = None) -> Path:
    """
    Smart rename for document storage.
    Applies smart naming based on doc_type and loan_name.
    """
    import re
    
    timestamp = datetime.now().strftime("%Y%m%d")
    
    stem = file_path.stem
    suffix = file_path.suffix.lower()
    
    clean_stem = clean_filename(stem, doc_type)
    
    parts = []
    if loan_name:
        parts.append(loan_name.replace(" ", "_"))
    parts.append(clean_stem)
    parts.append(timestamp)
    
    new_name = "_".join(parts) + suffix
    
    parent = file_path.parent
    new_path = parent / new_name
    
    counter = 1
    while new_path.exists():
        new_path = parent / f"{new_name[:-len(suffix)]}_{counter}{suffix}"
        counter += 1
    
    if new_path != file_path:
        try:
            import shutil
            shutil.move(str(file_path), str(new_path))
            log_operation("RENAME", str(new_path), f"Smart renamed from {file_path.name}")
        except Exception:
            new_path = file_path
    
    return new_path


def rename_for_loan(
    src_path: Path,
    loan_id: str = None,
    doc_type: str = None,
    date: datetime = None
) -> Path:
    """
    Rename file for loan folder with standard naming convention.
    Format: {loan_id}_{doc_type}_{YYYYMMDD}.pdf
    """
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime("%Y%m%d")
    
    doc_type_clean = (doc_type or "Doc").replace(" ", "")
    
    if loan_id:
        new_name = f"{loan_id}_{doc_type_clean}_{date_str}.pdf"
    else:
        new_name = f"{doc_type_clean}_{date_str}.pdf"
    
    new_path = src_path.parent / new_name
    
    counter = 1
    while new_path.exists():
        if loan_id:
            new_path = src_path.parent / f"{loan_id}_{doc_type_clean}_{date_str}_{counter}.pdf"
        else:
            new_path = src_path.parent / f"{doc_type_clean}_{date_str}_{counter}.pdf"
        counter += 1
    
    if new_path != src_path:
        try:
            import shutil
            shutil.move(str(src_path), str(new_path))
            log_operation("RENAME", str(new_path), f"Renamed to loan format")
        except Exception:
            new_path = src_path
    
    return new_path


def init():
    """Initialize folder structure. Call on app startup."""
    created = ensure_base_structure()
    if created:
        log_operation("INIT", str(BASE_DIR), f"Created: {', '.join(created)}")
    return BASE_DIR

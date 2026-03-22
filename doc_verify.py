"""
Quick Doc Verify — Processor Traien
Checks any incoming PDF in seconds:
  - Figures out what type of document it is
  - Counts pages
  - Finds the freshest date and tells you how old it is
  - Fuzzy-matches borrower name against your pipeline
  - Returns a staged "Pending Review" card — you confirm, nothing auto-saves

Works for email attachments (called from email_watch.py)
and manually uploaded files (called from the Document Scanner).
100% offline — regex + pypdf only.
"""

import re
import io
from datetime import date, datetime

try:
    from pypdf import PdfReader
    _PYPDF = True
except ImportError:
    _PYPDF = False


# ─────────────────────────────────────────────────────────────────────────────
# Document type keywords — order matters (most specific first)
# ─────────────────────────────────────────────────────────────────────────────
_DOC_TYPES = [
    ("Pay Stub",           ["pay stub", "paystub", "pay period", "earnings statement",
                            "gross pay", "net pay", "ytd earnings"]),
    ("W-2",                ["wages, tips", "w-2 wage", "employer's ein", "allocated tips"]),
    ("1099",               ["1099-misc", "1099-nec", "nonemployee compensation", "1099 income"]),
    ("VOE",                ["verification of employment", "voe", "dates of employment",
                            "employment verified"]),
    ("Bank Statement",     ["bank statement", "account statement", "beginning balance",
                            "ending balance", "deposits and additions", "checks paid",
                            "available balance", "daily ledger"]),
    ("Appraisal",          ["appraisal report", "uniform residential appraisal",
                            "subject property", "comparable sales", "1004", "urar"]),
    ("1003 Application",   ["uniform residential loan application", "borrower's name",
                            "1003", "urar application"]),
    ("Purchase Contract",  ["purchase agreement", "purchase contract", "real estate purchase",
                            "seller agrees", "buyer agrees", "earnest money deposit"]),
    ("Approval Letter",    ["conditional approval", "commitment letter", "loan approval",
                            "subject to the following", "prior to closing"]),
    ("Title Document",     ["title commitment", "title insurance", "schedule a", "schedule b",
                            "cpl", "closing protection letter"]),
    ("Closing Disclosure", ["closing disclosure", "loan costs", "other costs",
                            "cash to close", "projected payments"]),
    ("Credit Report",      ["credit report", "equifax", "experian", "transunion",
                            "tradeline", "fico score", "credit score"]),
    ("Insurance Doc",      ["homeowner's insurance", "hazard insurance", "declarations page",
                            "coverage amount", "policy number", "insured property"]),
    ("Loan Estimate",      ["loan estimate", "estimated total monthly payment",
                            "comparisons", "in 5 years"]),
    ("Tax Return",         ["u.s. individual income tax", "form 1040", "adjusted gross income",
                            "total income", "irs"]),
]

# How many pages we expect per doc type (min, ideal)
_PAGE_EXPECTATIONS = {
    "Bank Statement":     (2, 3,  "2–3 pages minimum"),
    "Pay Stub":           (1, 2,  "1–2 pages typical"),
    "W-2":                (1, 1,  "1 page per employer"),
    "1099":               (1, 1,  "1 page per payer"),
    "VOE":                (1, 2,  "1–2 pages typical"),
    "Appraisal":          (8, 15, "8+ pages expected"),
    "1003 Application":   (5, 9,  "5–9 pages typical"),
    "Purchase Contract":  (4, 20, "4+ pages expected"),
    "Approval Letter":    (2, 6,  "2+ pages typical"),
    "Credit Report":      (3, 12, "3+ pages typical"),
    "Closing Disclosure": (3, 5,  "3–5 pages typical"),
    "Loan Estimate":      (3, 3,  "3 pages standard"),
    "Tax Return":         (2, 6,  "2+ pages"),
}

# Month abbreviation → number
_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
    "oct": 10, "nov": 11, "dec": 12,
}


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def verify(pdf_bytes: bytes, filename: str = "", borrower_hint: str = "") -> dict:
    """
    Run quick verification on a PDF.
    Returns a dict with all checks + a suggestion card the UI can display.

    borrower_hint: name from email sender / subject (used alongside PDF text for matching)
    """
    text, page_count = _read_pdf(pdf_bytes)

    doc_type     = _guess_type(text, filename)
    dates        = _extract_dates(text)
    freshest     = max(dates) if dates else None
    days_old     = (date.today() - freshest).days if freshest else None
    date_status  = _date_flag(days_old, doc_type)
    page_status  = _page_flag(page_count, doc_type)
    match        = _match_borrower(text, filename, borrower_hint)

    flags   = []
    ok_list = []

    # ── Date check ───────────────────────────────────────────────────────────
    if freshest is None:
        flags.append("No recognisable dates found — verify manually")
    elif date_status == "fresh":
        ok_list.append(f"Dates current ({freshest.strftime('%b %d, %Y')} — {days_old}d ago)")
    elif date_status == "acceptable":
        ok_list.append(f"Dates ok ({freshest.strftime('%b %d, %Y')} — {days_old}d ago)")
    else:
        flags.append(f"Date may be stale: {freshest.strftime('%b %d, %Y')} ({days_old} days ago)")

    # ── Page check ───────────────────────────────────────────────────────────
    exp = _PAGE_EXPECTATIONS.get(doc_type)
    if exp:
        min_pages, _, note = exp
        if page_count < min_pages:
            flags.append(f"Only {page_count} page(s) — {note}")
        else:
            ok_list.append(f"{page_count} page(s) — looks complete")
    else:
        ok_list.append(f"{page_count} page(s)")

    # ── Borrower match ───────────────────────────────────────────────────────
    sugg = match.get("suggestion")
    if sugg == "match":
        ok_list.append(
            f"Name matches {match['borrower']} (Loan {match['loan_num']}) "
            f"— {match['confidence']}% confidence"
        )
    elif sugg == "possible":
        flags.append(
            f"Possible match: {match['borrower']} (Loan {match['loan_num']}) "
            f"— {match['confidence']}% — double-check"
        )
    else:
        flags.append("No pipeline borrower match — assign manually")

    # ── Overall verdict ───────────────────────────────────────────────────────
    if not flags and sugg == "match":
        verdict = "pass"          # all clear, high confidence
    elif len(flags) <= 1 and sugg in ("match", "possible"):
        verdict = "review"        # minor flag but probably right
    else:
        verdict = "check"         # needs human attention

    return {
        # Raw extractions
        "doc_type":       doc_type,
        "page_count":     page_count,
        "freshest_date":  str(freshest) if freshest else None,
        "days_old":       days_old,
        "date_status":    date_status,
        "page_status":    page_status,
        # Borrower match
        "loan_id":          match.get("loan_id"),
        "loan_num":         match.get("loan_num", ""),
        "borrower":         match.get("borrower", ""),
        "confidence":       match.get("confidence", 0),
        "suggestion":       sugg,
        "suggested_folder": match.get("suggested_folder", ""),
        # Summary for UI
        "verdict":   verdict,    # "pass" | "review" | "check"
        "ok_list":   ok_list,
        "flags":     flags,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PDF reading
# ─────────────────────────────────────────────────────────────────────────────

def _read_pdf(pdf_bytes: bytes) -> tuple[str, int]:
    if not _PYPDF:
        return "", 0
    try:
        rdr = PdfReader(io.BytesIO(pdf_bytes))
        pages = len(rdr.pages)
        text  = ""
        for pg in rdr.pages[:5]:       # read up to 5 pages for verification
            text += (pg.extract_text() or "") + "\n"
        return text, pages
    except Exception:
        return "", 0


# ─────────────────────────────────────────────────────────────────────────────
# Document type guessing
# ─────────────────────────────────────────────────────────────────────────────

def _guess_type(text: str, filename: str) -> str:
    blob = (text + " " + filename).lower()
    for dtype, keywords in _DOC_TYPES:
        if any(kw in blob for kw in keywords):
            return dtype
    return "Document"


# ─────────────────────────────────────────────────────────────────────────────
# Date extraction
# ─────────────────────────────────────────────────────────────────────────────

def _extract_dates(text: str) -> list[date]:
    today  = date.today()
    cutoff = date(2018, 1, 1)     # ignore dates before 2018
    found  = set()

    # MM/DD/YYYY or M/D/YYYY
    for m in re.finditer(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', text):
        try:
            d = date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
            if cutoff <= d <= today:
                found.add(d)
        except ValueError:
            pass

    # Month DD, YYYY  or  DD Month YYYY
    mth_pat = r'(' + '|'.join(_MONTHS.keys()) + r')'
    for m in re.finditer(
        rf'\b{mth_pat}\.?\s+(\d{{1,2}}),?\s+(\d{{4}})\b',
        text, re.IGNORECASE,
    ):
        try:
            mn = _MONTHS[m.group(1).lower()]
            d  = date(int(m.group(3)), mn, int(m.group(2)))
            if cutoff <= d <= today:
                found.add(d)
        except ValueError:
            pass

    # YYYY-MM-DD
    for m in re.finditer(r'\b(\d{4})-(\d{2})-(\d{2})\b', text):
        try:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if cutoff <= d <= today:
                found.add(d)
        except ValueError:
            pass

    return sorted(found)


# ─────────────────────────────────────────────────────────────────────────────
# Freshness flags
# ─────────────────────────────────────────────────────────────────────────────

def _date_flag(days_old: int | None, doc_type: str) -> str:
    if days_old is None:
        return "unknown"
    # Bank statements and pay stubs need to be very fresh
    strict = doc_type in ("Bank Statement", "Pay Stub", "VOE")
    if strict:
        if days_old <= 30:  return "fresh"
        if days_old <= 60:  return "acceptable"
        return "stale"
    else:
        if days_old <= 90:  return "fresh"
        if days_old <= 180: return "acceptable"
        return "stale"


def _page_flag(page_count: int, doc_type: str) -> str:
    exp = _PAGE_EXPECTATIONS.get(doc_type)
    if not exp:
        return "ok"
    min_pages, _, _ = exp
    if page_count < min_pages:
        return "short"
    return "ok"


# ─────────────────────────────────────────────────────────────────────────────
# Borrower → pipeline matching
# ─────────────────────────────────────────────────────────────────────────────

def _match_borrower(text: str, filename: str, hint: str) -> dict:
    try:
        from crm import get_all_loans
        loans = get_all_loans()
    except Exception:
        loans = []

    if not loans:
        return _no_match()

    try:
        from thefuzz import fuzz
        _fuzzy = True
    except ImportError:
        _fuzzy = False

    blob = f"{text} {filename} {hint}".lower()
    best_loan  = None
    best_score = 0

    for loan in loans:
        bname = loan.get("borrower", "").strip()
        if not bname:
            continue

        if bname.lower() in blob:
            score = 95
        elif _fuzzy:
            words  = [w for w in bname.lower().split() if len(w) > 2]
            scores = [fuzz.partial_ratio(w, blob) for w in words]
            score  = max(scores) if scores else 0
        else:
            # Check last name at least
            last = bname.split()[-1].lower()
            score = 80 if last in blob else 0

        if score > best_score:
            best_score = score
            best_loan  = loan

    if best_score >= 80 and best_loan:
        return {
            "loan_id":          best_loan.get("id"),
            "loan_num":         best_loan.get("loan_num", ""),
            "borrower":         best_loan.get("borrower", ""),
            "confidence":       best_score,
            "suggestion":       "match",
            "suggested_folder": best_loan.get("folder_path", ""),
        }
    if best_score >= 50 and best_loan:
        return {
            "loan_id":          best_loan.get("id"),
            "loan_num":         best_loan.get("loan_num", ""),
            "borrower":         best_loan.get("borrower", ""),
            "confidence":       best_score,
            "suggestion":       "possible",
            "suggested_folder": best_loan.get("folder_path", ""),
        }
    return _no_match()


def _no_match() -> dict:
    return {
        "loan_id": None, "loan_num": "", "borrower": None,
        "confidence": 0, "suggestion": "unknown", "suggested_folder": "",
    }

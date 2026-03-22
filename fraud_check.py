"""
Fraud Check — Processor Traien
Scans W-2, pay stub, and bank statement PDFs for common fraud indicators.
Flags if 2+ clues are found. 100% offline — regex only, no AI.

Checks:
  1. Multiple SSNs — more than one unique SSN in the same document
  2. Zero federal withholding with nonzero net pay
  3. Balance jump — ending balance > 2.5x beginning balance on a bank statement
  4. Uniform pay — same exact net pay amount repeating (round-number fabrication)
  5. Missing months — gap > 35 days between dates found in the document
  6. Employer name inconsistency — multiple different employer names in one doc
  7. Round-dollar income — suspiciously round gross income figures
"""

import re
import io
from datetime import date, timedelta

try:
    from pypdf import PdfReader
    _PYPDF = True
except ImportError:
    _PYPDF = False


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def check(pdf_bytes: bytes, doc_type: str = "") -> dict:
    """
    Run fraud checks on a PDF.
    Returns:
        flags      — list of dicts: {rule, detail, severity}
        risk_level — "high" (3+ flags), "medium" (2 flags), "low" (0-1 flag)
        summary    — one-line plain English description
    """
    text = _read(pdf_bytes)
    if not text:
        return _result([], note="Could not extract text — manual review required")

    dtype = doc_type.lower()
    flags = []

    # Run all applicable checks
    flags += _check_multiple_ssn(text)
    flags += _check_zero_withholding(text, dtype)
    flags += _check_balance_jump(text, dtype)
    flags += _check_uniform_pay(text, dtype)
    flags += _check_date_gap(text)
    flags += _check_employer_inconsistency(text, dtype)
    flags += _check_round_income(text, dtype)

    # Severity → risk level
    highs = sum(1 for f in flags if f["severity"] == "high")
    meds  = sum(1 for f in flags if f["severity"] == "medium")
    total = len(flags)

    if highs >= 2 or total >= 3:
        risk = "high"
    elif total >= 2 or highs >= 1:
        risk = "medium"
    else:
        risk = "low"

    return _result(flags, risk)


def _result(flags, risk="low", note=""):
    count = len(flags)
    if note:
        summary = note
    elif risk == "high":
        summary = f"⚠️ HIGH RISK — {count} fraud indicator(s) found — flag for underwriter review"
    elif risk == "medium":
        summary = f"⚠️ MEDIUM — {count} indicator(s) — review carefully before clearing"
    elif count == 0:
        summary = "✅ No fraud indicators detected"
    else:
        summary = f"ℹ️ 1 minor indicator — verify manually"

    return {"flags": flags, "risk_level": risk, "summary": summary, "flag_count": count}


# ─────────────────────────────────────────────────────────────────────────────
# PDF reader
# ─────────────────────────────────────────────────────────────────────────────

def _read(pdf_bytes: bytes) -> str:
    if not _PYPDF:
        return ""
    try:
        rdr  = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for pg in rdr.pages:
            text += (pg.extract_text() or "") + "\n"
        return text
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Rule 1 — Multiple SSNs in one document
# ─────────────────────────────────────────────────────────────────────────────

def _check_multiple_ssn(text: str) -> list:
    ssns = set(re.findall(r"\b(\d{3}-\d{2}-\d{4})\b", text))
    # Remove obviously fake/placeholder SSNs
    ssns = {s for s in ssns if not s.startswith("000") and not s.startswith("999")}
    if len(ssns) > 1:
        return [{
            "rule":     "Multiple SSNs",
            "detail":   f"{len(ssns)} different SSNs found: {', '.join(sorted(ssns))}",
            "severity": "high",
        }]
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Rule 2 — Zero federal/state withholding with positive net pay
# ─────────────────────────────────────────────────────────────────────────────

def _check_zero_withholding(text: str, dtype: str) -> list:
    if "bank" in dtype:
        return []  # not applicable to bank statements

    zero_pat = re.compile(
        r"(?:federal\s+(?:tax|withholding|income\s+tax)|fit\b|state\s+(?:tax|withholding)|sit\b)"
        r"\s*[:\-]?\s*\$?\s*0+(?:\.0+)?\b",
        re.IGNORECASE,
    )
    net_pay_pat = re.compile(
        r"(?:net\s+pay|net\s+earnings|take\s+home)\s*[:\-]?\s*\$?\s*([\d,]+(?:\.\d{2})?)",
        re.IGNORECASE,
    )

    zero_matches = zero_pat.findall(text)
    net_matches  = net_pay_pat.findall(text)

    if zero_matches:
        net_vals = []
        for m in net_matches:
            try:
                net_vals.append(float(m.replace(",", "")))
            except ValueError:
                pass
        has_income = any(v > 0 for v in net_vals)
        if has_income:
            return [{
                "rule":     "Zero Withholding / Tax",
                "detail":   "Federal or state tax shows $0 but net pay is positive — verify with borrower",
                "severity": "high",
            }]
        return [{
            "rule":     "Zero Withholding",
            "detail":   "Tax withholding appears to be $0 — verify this is intentional",
            "severity": "medium",
        }]
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Rule 3 — Balance jump (bank statement)
# ─────────────────────────────────────────────────────────────────────────────

def _check_balance_jump(text: str, dtype: str) -> list:
    if "bank" not in dtype and "statement" not in dtype:
        return []

    begin_pat = re.compile(
        r"(?:beginning\s+balance|opening\s+balance|balance\s+forward|previous\s+balance)"
        r"\s*[:\-]?\s*\$?\s*([\d,]+(?:\.\d{2})?)",
        re.IGNORECASE,
    )
    end_pat = re.compile(
        r"(?:ending\s+balance|closing\s+balance|balance\s+as\s+of|available\s+balance)"
        r"\s*[:\-]?\s*\$?\s*([\d,]+(?:\.\d{2})?)",
        re.IGNORECASE,
    )

    begins = [float(m.replace(",", "")) for m in begin_pat.findall(text)]
    ends   = [float(m.replace(",", "")) for m in end_pat.findall(text)]

    if begins and ends:
        beg = begins[0]
        end = ends[-1]
        if beg > 100 and end > beg * 2.5:
            return [{
                "rule":     "Unusual Balance Jump",
                "detail":   f"Opening ${beg:,.2f} → Closing ${end:,.2f} "
                            f"({end/beg:.1f}x increase) — verify large deposit source",
                "severity": "high",
            }]
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Rule 4 — Uniform / identical pay (possible fabrication)
# ─────────────────────────────────────────────────────────────────────────────

def _check_uniform_pay(text: str, dtype: str) -> list:
    if "bank" in dtype:
        return []

    net_pat = re.compile(
        r"(?:net\s+pay|take\s+home|net\s+earnings)\s*[:\-]?\s*\$?\s*([\d,]+\.\d{2})",
        re.IGNORECASE,
    )
    vals = []
    for m in net_pat.findall(text):
        try:
            vals.append(float(m.replace(",", "")))
        except ValueError:
            pass

    if len(vals) >= 3:
        unique = set(round(v, 2) for v in vals)
        if len(unique) == 1:
            return [{
                "rule":     "Identical Pay Every Period",
                "detail":   f"Net pay is exactly ${vals[0]:,.2f} every period — "
                            f"unusual for hourly workers, verify pay stubs",
                "severity": "medium",
            }]
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Rule 5 — Date gaps > 35 days (missing month)
# ─────────────────────────────────────────────────────────────────────────────

_MONTHS_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _check_date_gap(text: str) -> list:
    today  = date.today()
    cutoff = date(2020, 1, 1)
    found  = set()

    for m in re.finditer(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", text):
        try:
            d = date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
            if cutoff <= d <= today:
                found.add(d)
        except ValueError:
            pass

    mth_k = "|".join(_MONTHS_MAP.keys())
    for m in re.finditer(rf"\b({mth_k})\.?\s+(\d{{1,2}}),?\s+(\d{{4}})\b", text, re.IGNORECASE):
        try:
            mn = _MONTHS_MAP[m.group(1).lower()]
            d  = date(int(m.group(3)), mn, int(m.group(2)))
            if cutoff <= d <= today:
                found.add(d)
        except ValueError:
            pass

    dates = sorted(found)
    if len(dates) >= 2:
        gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        max_gap = max(gaps)
        if max_gap > 35:
            return [{
                "rule":     "Date Gap in Document",
                "detail":   f"Largest gap between dates: {max_gap} days — possible missing statement period",
                "severity": "medium",
            }]
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Rule 6 — Multiple employer names in one pay stub
# ─────────────────────────────────────────────────────────────────────────────

def _check_employer_inconsistency(text: str, dtype: str) -> list:
    if "bank" in dtype:
        return []

    employer_pat = re.compile(
        r"(?:employer(?:'s)?\s+name|company\s+name|employer)[:\s]+([^\n]{3,50})",
        re.IGNORECASE,
    )
    employers = list({m.strip().lower() for m in employer_pat.findall(text)})

    if len(employers) >= 3:
        return [{
            "rule":     "Multiple Employer Names",
            "detail":   f"{len(employers)} different employer names found in one document — verify",
            "severity": "medium",
        }]
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Rule 7 — Suspiciously round gross income
# ─────────────────────────────────────────────────────────────────────────────

def _check_round_income(text: str, dtype: str) -> list:
    if "bank" in dtype:
        return []

    gross_pat = re.compile(
        r"(?:gross\s+(?:pay|earnings|income|wages)|gross\s+ytd)\s*[:\-]?\s*\$?\s*([\d,]+)(?:\.00)?",
        re.IGNORECASE,
    )
    vals = []
    for m in gross_pat.findall(text):
        try:
            v = float(m.replace(",", ""))
            if v > 1000:
                vals.append(v)
        except ValueError:
            pass

    # Flag if all values are multiples of 1000 and there are 2+
    if len(vals) >= 2:
        round_count = sum(1 for v in vals if v % 1000 == 0)
        if round_count == len(vals) and len(vals) >= 2:
            return [{
                "rule":     "Round-Dollar Income Figures",
                "detail":   f"All {len(vals)} gross income values are exact multiples of $1,000 — "
                            f"may indicate fabricated amounts",
                "severity": "medium",
            }]
    return []

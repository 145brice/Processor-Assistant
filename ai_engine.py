"""
Offline Processing Engine for Processor Assistant
100% local - no API calls, no cloud, no AI.
Uses regex + pattern matching to analyze mortgage documents.
Spaced out processing to be easy on the CPU.
"""

import re
import time
import io
from pypdf import PdfReader


# ---------------------------------------------------------------------------
# PDF Text Extraction (in memory, never saved to disk)
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes in memory. 2-sec pause per page to stay light."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
        time.sleep(0.05)  # gentle pause per page - no CPU spike
    return text.strip()


# ---------------------------------------------------------------------------
# Condition Extraction — reads the ACTUAL lines from the PDF
# ---------------------------------------------------------------------------

# Pre-compiled regex for junk line detection
_JUNK_NUMERIC = re.compile(r'^[\$\d\s,\.\-\/\(\)%]+$')
_JUNK_EMAIL = re.compile(r'^[\w.+-]+@[\w\-]+\.[\w.]+$')
_JUNK_PHONE = re.compile(r'^[\(\)\d\s\-\.]+$')
_JUNK_ADDRESS = re.compile(r'^\d+\s+[A-Z][a-z]+\s+(?:Dr|St|Ave|Blvd|Rd|Ln|Ct|Way|Cir|Pl)')
_JUNK_CITY_STATE = re.compile(r'^[A-Za-z\s]+,\s*[A-Z]{2},?\s*\d{5}')
_JUNK_NAME = re.compile(r'^[A-Z][a-z]+\s+[A-Z][a-z]+(?:\-[A-Z][a-z]+)?$')
_JUNK_CORP = re.compile(r'(?i)^(?:NEXA|Orion|American Financial|LLC|Inc|DBA)\b')
_JUNK_SUMMARY = re.compile(r'(?i)^(?:Purchase Price|Refinance|Estimated|Lender (?:Fee|Credit)|Seller Credit|Other Credit|Subordinate|Loan Amount|Cash (?:from|to)|Total Cost|Last UW|Date.?Time)')
_JUNK_CODE = re.compile(r'^(?:Underwriter|Jr Underwriter|Closer|Manager|Processor|Sr Underwriter)\s+W[A-Z]{2}\d{2}\s*$')
_JUNK_RESPONSIBLE = re.compile(r'(?i)^(?:Orion\s*)?Responsible\s*\d')
_JUNK_TIMESTAMP = re.compile(r'(?i)^(?:Last UW|Date.?Time)\s')
_JUNK_PRODUCT = re.compile(r'^[A-Z]{3,5}\d{2}\s')
_JUNK_MORTGAGEE = re.compile(r'(?i)^(?:S\.?A\.?O\.?A|I\.?S\.?A\.?O\.?A)')
_JUNK_MASKED = re.compile(r'^X{3,}\d+$')
_JUNK_BOILERPLATE = re.compile(r'(?i)(?:must be received from the broker within|calendar days of the initial|closed for incompleteness)')
_JUNK_WAIVED = re.compile(r'(?i)^(?:Not Waived|Past Due|contact your|Account Manager)$')
_CONDITION_ACTION = re.compile(
    r'(?i)\b(?:provide|submit|obtain|furnish|verify|document|explain|clear|'
    r'resolve|update|upload|supply|confirm|complete|correct|evidence|copy of|'
    r'letter of|payoff|title|insurance|hoi|hazard|flood|appraisal|voe|bank statement|'
    r'paystub|pay stub|w-?2|tax return|lease|gift letter)\b'
)
_CONDITION_OBJECT = re.compile(
    r'(?i)\b(?:paystubs?|pay\s*stubs?|bank statements?|asset statements?|'
    r'w-?2s?|1099s?|tax returns?|tax transcripts?|voe|v[oe]m|loe|letter of explanation|'
    r'gift letters?|title commitment|title policy|survey|payoff|subordination|'
    r'homeowners?|hazard|hoi|flood|insurance|appraisal|inspection|purchase contract|'
    r'closing disclosure|cd|driver.?s license|photo id|ssn|social security|'
    r'mortgage statement|rent verification|lease agreement|earnest money|emd)\b'
)
_APPROVAL_NON_CONDITION = re.compile(
    r'(?i)^(?:borrower|co-?borrower|loan\s*(?:number|amount|purpose|type)|'
    r'property|subject property|purchase price|interest rate|ltv|cltv|dti|'
    r'program|product|uwm|united wholesale|loan approval|approval|approved|decision|'
    r'broker|loan officer|account executive|date|expiration|expires|'
    r'prior to closing|prior to docs|prior to funding|conditions?|'
    r'ptd conditions?|ptf conditions?|summary|notes?|message|page\s+\d+)\b'
)


def _is_junk_line(text: str) -> bool:
    """Return True if this line is NOT a real condition — it's metadata/junk."""
    t = text.strip()
    # Too short
    if len(t) < 12:
        return True
    # Pure numbers / dollar amounts / dates
    if _JUNK_NUMERIC.match(t):
        return True
    # Email addresses
    if _JUNK_EMAIL.match(t):
        return True
    # Phone numbers only
    if _JUNK_PHONE.match(t):
        return True
    # Street addresses (number + street name pattern)
    if _JUNK_ADDRESS.match(t):
        return True
    # City, State, Zip
    if _JUNK_CITY_STATE.match(t):
        return True
    # Just a person's name (2-3 words, all capitalized, no action verbs)
    if _JUNK_NAME.match(t):
        return True
    # Company/lender names on their own line
    if _JUNK_CORP.match(t):
        return True
    # Closing cost summary labels
    if _JUNK_SUMMARY.match(t):
        return True
    # Condition code only (no description after it)
    if _JUNK_CODE.match(t):
        return True
    # "Orion Responsible" / date-only tails
    if _JUNK_RESPONSIBLE.match(t):
        return True
    # Timestamps
    if _JUNK_TIMESTAMP.match(t):
        return True
    # Loan product codes
    if _JUNK_PRODUCT.match(t) and len(t) < 25:
        return True
    # Mortgagee/Loss payee clause (address block, not a condition)
    if _JUNK_MORTGAGEE.match(t):
        return True
    # Masked account numbers
    if _JUNK_MASKED.match(t):
        return True
    # Boilerplate footer lines
    if _JUNK_BOILERPLATE.search(t):
        return True
    # "Not Waived", "Past Due - Please", "contact your", "Account Manager"
    if _JUNK_WAIVED.match(t):
        return True
    return False


def _is_real_condition_text(text: str, *, approval_only: bool = False) -> bool:
    t = re.sub(r'\s+', ' ', str(text or '')).strip()
    if _is_junk_line(t):
        return False
    if approval_only and _APPROVAL_NON_CONDITION.match(t):
        return False
    if len(t.split()) < 3:
        return False
    return bool(_CONDITION_ACTION.search(t) or (approval_only and _CONDITION_OBJECT.search(t)))


def _approval_condition_candidate(text: str) -> bool:
    t = re.sub(r'\s+', ' ', str(text or '')).strip()
    if not _is_real_condition_text(t, approval_only=True) and not _CONDITION_OBJECT.search(t):
        return False
    if _APPROVAL_NON_CONDITION.match(t):
        return False
    if re.search(r'(?i)\b(?:prepared for|contact name|email:|phone:|date printed|senior uw|account manager)\b', t):
        return False
    return True


def _is_approval_metadata_line(text: str) -> bool:
    """Skip approval-letter header/loan-summary lines without rejecting terse conditions."""
    t = re.sub(r'\s+', ' ', str(text or '')).strip()
    if not t:
        return True
    if re.search(r'(?i)\b(?:prepared for|contact name|email:|phone:|date printed|senior uw|account manager)\b', t):
        return True
    if re.match(
        r'(?i)^(?:borrower|co-?borrower|loan\s*(?:number|amount|purpose|type)|'
        r'property|subject property|purchase price|interest rate|ltv|cltv|dti|'
        r'program|product|uwm|united wholesale|loan approval|approval|approved|'
        r'decision|broker|loan officer|date|expiration|expires|page\s+\d+)\b',
        t,
    ):
        return True
    return False


def extract_conditions(pdf_text: str, doc_type: str, user_history=None) -> str:
    """
    Extract conditions by reading the actual text from the PDF.

    Handles two main formats:
      A) Lender condition codes: lines starting with a role + code like
         "Underwriter WCR01", "Closer WES03", "Jr Underwriter WPR15"
         followed by the condition description (possibly spanning multiple lines).
      B) Traditional: numbered/bulleted lists, or "Prior to Closing:" sections.

    Aggressively filters out junk (addresses, dollar amounts, emails, closing
    cost summaries, timestamps, boilerplate).
    """
    conditions = []
    cond_num = 0
    seen = set()

    lines = pdf_text.split("\n")

    # UWM and similar approval letters often list conditions as noun phrases
    # rather than action sentences ("Most recent 30 days paystubs", etc.).
    approval_mode = doc_type in {"Approval Letter", "Broker Package (BP)"}
    if approval_mode:
        condition_heading = re.compile(
            r'(?i)\b(?:loan\s+approval\s+conditions?|approval\s+conditions?|'
            r'ptd\s+conditions?|ptf\s+conditions?|prior\s+to\s+(?:closing|docs|funding)\s+conditions?|'
            r'conditions?\s+(?:of\s+approval|list|summary))\b'
        )
        for idx, line in enumerate(lines):
            if condition_heading.search(line.strip()):
                lines = lines[idx + 1:]
                break

    # ---------------------------------------------------------------
    # FORMAT A: Lender condition-code format
    # Matches: "Underwriter WCR01", "Jr Underwriter WPR15", "Closer WES03",
    #          "Manager WCL02", "Processor WXX01", etc.
    # ---------------------------------------------------------------
    code_start = re.compile(
        r'^(?:Sr\s+|Jr\s+)?'
        r'(?:Underwriter|Closer|Manager|Processor)\s+'
        r'(W[A-Z]{2}\d{2})\b'
    )
    # Also match bare condition codes without role prefix: "WCR32 ..."
    bare_code = re.compile(r'^(W[A-Z]{2}\d{2})\s+')
    # Also match loan-number-prefixed rows: "5000002228902-Appraisal ..."
    loan_prefix = re.compile(r'^\d{8,}\s*[\-–]\s*')

    found_code_format = False
    current_cond = None  # accumulates multi-line condition text

    def _flush_condition(cond_obj):
        """Save the accumulated condition if it's real."""
        nonlocal cond_num
        if not cond_obj:
            return
        desc = cond_obj["desc"].strip()
        # Remove leading dates that got concatenated from continuation lines
        desc = re.sub(r'^\d{1,2}/\d{1,2}/\d{2,4}\s*', '', desc).strip()
        # Remove "(No action required)" prefix but keep the rest
        desc = re.sub(r'^\(No action required\)\s*', '', desc).strip()
        # Remove "Orion Responsible" fragments that snuck in
        desc = re.sub(r'(?i)^(?:Orion\s+)?Responsible\s*', '', desc).strip()
        # Remove leading dates again (in case Responsible removal exposed one)
        desc = re.sub(r'^\d{1,2}/\d{1,2}/\d{2,4}\s*', '', desc).strip()
        if doc_type == "Approval Letter":
            if _is_junk_line(desc) or _is_approval_metadata_line(desc) or len(desc) < 12:
                return
        elif not _is_real_condition_text(desc):
            return
        lower = desc.lower()
        if lower in seen:
            return
        seen.add(lower)
        cond_num += 1
        conditions.append({
            "num": str(cond_num),
            "desc": desc,
            "party": cond_obj["party"],
            "status": cond_obj["status"],
        })

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # Check for condition code header
        code_m = code_start.match(line)
        if code_m:
            found_code_format = True
            # Flush previous condition
            _flush_condition(current_cond)

            code = code_m.group(1)
            # The rest of the line after the code is the start of description
            rest = line[code_m.end():].strip()

            # Determine responsible party from the role prefix
            party = "Underwriter"
            if line.startswith("Closer"):
                party = "Closer"
            elif line.startswith("Manager"):
                party = "Manager"
            elif line.startswith("Processor"):
                party = "Processor"

            # Extract status if present
            status = "Needed"
            sm = re.search(r'(?i)\b(Needed|Received|Cleared|Waived|Pending|Satisfied)\b', rest)
            if sm:
                status = sm.group(1).capitalize()

            # Clean the description: strip "Orion Responsible", dates, status words
            rest = re.sub(r'(?i)\b(?:Orion\s+)?Responsible\b', '', rest).strip()
            rest = re.sub(r'(?i)\b(?:Needed|Received|Cleared|Waived|Pending|Satisfied)\b', '', rest).strip()
            rest = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '', rest).strip()
            rest = re.sub(r'^\s*[\-–]\s*', '', rest).strip()

            current_cond = {"desc": rest, "party": party, "status": status, "code": code}
            continue

        # Check for bare condition code (no role prefix): "WCR32 ..."
        bare_m = bare_code.match(line)
        if bare_m and found_code_format:
            _flush_condition(current_cond)
            rest = line[bare_m.end():].strip()
            rest = re.sub(r'(?i)\b(?:Needed|Received|Cleared|Waived|Pending|Satisfied)\b', '', rest).strip()
            rest = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '', rest).strip()
            current_cond = {"desc": rest, "party": "Borrower", "status": "Needed", "code": bare_m.group(1)}
            sm = re.search(r'(?i)\b(Needed|Received|Cleared|Waived|Pending|Satisfied)\b', line)
            if sm:
                current_cond["status"] = sm.group(1).capitalize()
            continue

        # Check for loan-number-prefixed rows
        loan_m = loan_prefix.match(line)
        if loan_m:
            found_code_format = True
            _flush_condition(current_cond)
            rest = line[loan_m.end():].strip()
            # Strip category tags and dates
            rest = re.sub(r'(?i)\s*(?:Legal|Property|Credit|Income|Asset|Compliance|Closing|Appraisal|Insurance|Title|Misc)\s*(?:Docs?)?\s*$', '', rest).strip()
            rest = re.sub(r'\s*\d{1,2}/\d{1,2}/\d{2,4}.*$', '', rest).strip()
            status = "Needed"
            sm = re.search(r'(?i)\b(Needed|Received|Cleared|Waived|Pending|Satisfied)\b', line)
            if sm:
                status = sm.group(1).capitalize()
            current_cond = {"desc": rest, "party": _guess_party(rest), "status": status, "code": ""}
            continue

        # If we're inside a code-format condition, this line is a continuation
        if found_code_format and current_cond is not None:
            # Stop at clear section breaks (closing cost summary, footer)
            if re.match(r'(?i)^(?:Estimated Cash to Close|Conditions must be received)', line):
                _flush_condition(current_cond)
                current_cond = None
                continue
            # Skip junk lines but DON'T flush — they might just be noise
            # between the condition header and its real description
            if _is_junk_line(line):
                continue
            # Skip "Responsible" / date-only lines (absorbed into current condition)
            if re.match(r'(?i)^(?:Orion\s+)?Responsible\s*(?:\d|$)', line):
                continue
            # Skip standalone date lines
            if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}\s*$', line):
                continue
            # Append to current condition
            current_cond["desc"] += " " + line

    # Flush last condition
    _flush_condition(current_cond)

    # ---------------------------------------------------------------
    # FORMAT B: Traditional numbered/bulleted/section-based conditions
    # Only runs if Format A didn't find anything
    # ---------------------------------------------------------------
    if not conditions:
        in_section = False
        section_start = re.compile(
            r'(?i)(?:prior\s+to\s+(?:closing|funding|docs|CTC|clear)|'
            r'loan\s+approval\s+conditions?|approval\s+conditions?|'
            r'conditions?\s*(?:of\s+approval|to\s+be\s+satisfied|list|:)|'
            r'outstanding\s+(?:conditions?|items?|requirements?)|'
            r'underwriting\s+conditions?|'
            r'items?\s+(?:needed|required|outstanding)|'
            r'requirements?\s*:)'
        )
        section_end = re.compile(
            r'(?i)^(?:sincerely|regards|thank\s+you|disclaimer|notice|'
            r'this\s+(?:letter|document|approval)|page\s+\d|'
            r'the\s+above\s+(?:loan|mortgage))\b'
        )

        if approval_mode:
            current_section_cond = None
            numbered_start = re.compile(r'^\s*(\d{1,3})[\.\)\:]\s*(.+)$')

            def _clean_approval_line(value: str) -> str:
                return re.sub(r'^[\s]*(?:[a-zA-Z][\.\)]|[\-\*\u2022])\s*', '', value).strip()

            def _flush_section_condition():
                nonlocal cond_num, current_section_cond
                if not current_section_cond:
                    return
                display_num = current_section_cond["num"]
                desc = re.sub(r'\s+', ' ', " ".join(current_section_cond["parts"])).strip()
                current_section_cond = None
                if _is_junk_line(desc) or _is_approval_metadata_line(desc) or len(desc) < 12:
                    return
                lower = desc.lower()
                if lower in seen:
                    return
                seen.add(lower)
                cond_num += 1
                conditions.append({
                    "num": display_num,
                    "desc": desc,
                    "party": _guess_party(desc),
                    "status": "Needed",
                })

            for raw_line in lines:
                line = raw_line.strip()
                if not line:
                    continue
                if section_start.search(line):
                    _flush_section_condition()
                    in_section = True
                    continue
                if in_section and section_end.search(line):
                    _flush_section_condition()
                    in_section = False
                    continue
                if not in_section:
                    continue

                num_match = numbered_start.match(line)
                if num_match:
                    _flush_section_condition()
                    first_text = _clean_approval_line(num_match.group(2))
                    if not (_is_junk_line(first_text) or _is_approval_metadata_line(first_text) or len(first_text) < 12):
                        current_section_cond = {"num": num_match.group(1), "parts": [first_text]}
                    continue

                cleaned = _clean_approval_line(line)
                if _is_junk_line(cleaned) or _is_approval_metadata_line(cleaned) or len(cleaned) < 12:
                    continue
                if current_section_cond:
                    current_section_cond["parts"].append(cleaned)
            _flush_section_condition()
        else:
            for raw_line in lines:
                line = raw_line.strip()
                if not line:
                    continue
                if section_start.search(line):
                    in_section = True
                    continue
                if in_section and section_end.search(line):
                    in_section = False
                    continue
                if in_section:
                    cleaned = re.sub(r'^[\s]*(?:\d{1,3}[\.\)\:]|[a-zA-Z][\.\)]|[\-\*\u2022])\s*', '', line).strip()
                    if not _is_real_condition_text(cleaned):
                        continue
                    if cleaned.lower() in seen:
                        continue
                    seen.add(cleaned.lower())
                    cond_num += 1
                    conditions.append({
                        "num": str(cond_num),
                        "desc": cleaned,
                        "party": _guess_party(cleaned),
                        "status": "Needed",
                    })

        # Also catch standalone action lines, but do not split approval continuation text
        # into extra checkboxes once numbered approval conditions were found.
        if not (approval_mode and conditions):
            for raw_line in lines:
                line = raw_line.strip()
                m = re.match(r'(?i)^\s*(?:\d{1,3}[\.\)\:]|[\-\*\u2022])?\s*(?:provide|submit|obtain|furnish)\s+(.{15,})', line)
                if m:
                    desc = m.group(1).strip().rstrip('.')
                    lower = desc.lower()
                    if approval_mode:
                        is_real = not (_is_junk_line(desc) or _is_approval_metadata_line(desc) or len(desc) < 12)
                    else:
                        is_real = _is_real_condition_text(desc)
                    if is_real and lower not in seen:
                        already = any(lower in s or s in lower for s in seen)
                        if not already:
                            seen.add(lower)
                            cond_num += 1
                            conditions.append({
                                "num": str(cond_num),
                                "desc": desc,
                                "party": _guess_party(desc),
                                "status": "Needed",
                            })

    time.sleep(0.3)

    # --- Build output ---
    if not conditions:
        return (
            "No specific conditions found in this document.\n\n"
            "**Possible reasons:**\n"
            "- The PDF may be a scanned image (text not extractable without OCR)\n"
            "- Conditions may use non-standard formatting\n"
            "- This document type may not contain conditions\n\n"
            "**Raw text preview (first 500 chars):**\n"
            f"```\n{pdf_text[:500]}\n```\n\n"
            "If you see condition text above, the formatting may need a custom pattern."
        )

    table_lines = [
        "| # | Condition | Responsible | Status |",
        "|---|-----------|-------------|--------|",
    ]
    for c in conditions:
        desc = c["desc"].replace("|", "/")
        table_lines.append(f"| {c['num']} | {desc} | {c['party']} | {c['status']} |")

    notes = (
        f"\n\n**{len(conditions)} condition(s) extracted from document.**\n"
        "- Each row above is actual text pulled from your PDF.\n"
        "- Select conditions below to draft emails."
    )
    return "\n".join(table_lines) + notes


def _guess_party(text: str) -> str:
    """Guess responsible party from condition description."""
    t = text.lower()
    if any(w in t for w in ["title", "lien", "survey", "estoppel", "hoa"]):
        return "Title"
    if any(w in t for w in ["apprais", "inspection"]):
        return "Appraiser"
    if any(w in t for w in ["underwrit", "approve", "clear to close"]):
        return "Underwriter"
    if any(w in t for w in ["insurance", "hazard", "flood"]):
        return "Insurance"
    return "Borrower"


# ---------------------------------------------------------------------------
# Bank Statement — Key Field Extraction
# ---------------------------------------------------------------------------

def extract_bank_statement_fields(pdf_text: str) -> dict:
    """
    Extract key fields from a bank statement.
    Handles PNC, Chase, BofA, Wells Fargo, US Bank, credit unions.
    PNC and many banks split labels/values across multiple lines — handled via
    line-context scanning in addition to inline regex.
    """
    t = pdf_text
    lines = [l.strip() for l in t.splitlines()]
    result = {
        "holder_names":      [],
        "account_number":    None,
        "institution":       None,
        "statement_month":   None,
        "period_start":      None,
        "period_end":        None,
        "beginning_balance": None,
        "ending_balance":    None,
        "lowest_balance":    None,
        "deposits_total":    None,
        "withdrawals_total": None,
    }

    def _dollars_on_line(line):
        """Return list of dollar amounts found on a line, commas stripped."""
        return [v.replace(",", "") for v in re.findall(r'[\d,]+\.\d{2}', line)]

    def _first_dollar_after(label_pat, text, window=200):
        """Find first dollar amount within window chars after a label match."""
        m = re.search(label_pat, text, re.IGNORECASE)
        if not m:
            return None
        snippet = text[m.end(): m.end() + window]
        amt = re.search(r'(?<!\d)([\d,]+\.\d{2})(?!\d)', snippet)
        return amt.group(1).replace(",", "") if amt else None

    # ── Institution ──────────────────────────────────────────────────────────
    # Named banks first, then generic pattern
    known = re.search(
        r'\b(PNC Bank|PNC|Chase|Bank of America|Wells Fargo|U\.?S\.? Bank|Citibank|'
        r'Truist|TD Bank|Capital One|Regions|SunTrust|BB&T|Fifth Third|KeyBank|'
        r'Huntington|Citizens Bank|Ally Bank|Navy Federal|USAA)\b',
        t[:800], re.IGNORECASE
    )
    if known:
        result["institution"] = known.group(1).strip()
    else:
        generic = re.search(
            r'^([A-Z][A-Za-z\s&]+(?:Bank|Credit Union|Financial|Savings|N\.A\.|FSB|FCU))',
            t[:400], re.MULTILINE
        )
        if generic:
            result["institution"] = generic.group(1).strip()

    # ── Account holder name(s) ───────────────────────────────────────────────
    names_found = []
    _skip = {"BANK", "ACCOUNT", "STATEMENT", "BALANCE", "CHECKING", "SAVINGS",
             "MEMBER", "FDIC", "INSURED", "PERIOD", "ENDING", "BEGINNING",
             "DEPOSIT", "SUMMARY", "ACTIVITY", "PAGE", "DATE", "ONLINE",
             "BANKING", "CUSTOMER", "SERVICE", "NUMBER", "VIRTUAL", "WALLET",
             "SPEND", "IMPORTANT", "INFORMATION", "DEBIT", "CARD", "TRANSACTION",
             "EFFECTIVE", "CONSUMER", "BUSINESS", "INTEREST"}

    # Pattern 1: explicit inline label — name must start with capital, 2+ words
    for pat in [
        r'(?i)(?:account\s*holder|primary\s*owner|name\s*on\s*account|account\s*name|prepared\s*for|statement\s*for)\s*[:\-]?\s*([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){1,4})',
        r'(?i)(?:account\s*of|owner)\s*[:\-]\s*([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){1,3})',
    ]:
        for m in re.finditer(pat, t):
            n = m.group(1).strip()
            # Must have at least 2 words and not be a common false-positive phrase
            words = n.split()
            if len(words) >= 2 and words[0] not in {"the", "a", "an", "this", "for"} and n not in names_found:
                names_found.append(n)

    # Pattern 2: ALL-CAPS name on its own line in first 80 lines (address block)
    for line in lines[:80]:
        # Must be 2-5 words, all caps, no skip words, no digits
        words = line.split()
        if 2 <= len(words) <= 5 and not re.search(r'\d', line):
            if all(re.match(r'^[A-Z][A-Z\'\-]+$', w) for w in words):
                if not any(w in _skip for w in words):
                    if line not in names_found:
                        names_found.append(line)

    # Pattern 3: Title-case "First Last" or "First M Last" on its own line
    _skip_title = {"Balance", "Summary", "Transaction", "Statement", "Account",
                   "Overdraft", "Coverage", "Period", "Service", "Information",
                   "Checking", "Savings", "Virtual", "Wallet", "Important"}
    for line in lines[:80]:
        if re.match(r'^[A-Z][a-z]+(\s+[A-Z]\.?)?\s+[A-Z][a-z]{2,}(\s+[A-Z][a-z]+)?$', line):
            words = line.split()
            if 2 <= len(words) <= 4 and not any(w in _skip_title for w in words) and line not in names_found:
                names_found.append(line)

    result["holder_names"] = names_found[:3]

    # ── Account number ───────────────────────────────────────────────────────
    acct_patterns = [
        # PNC style: "Primary account number: 47-2448-2728"
        r'(?i)(?:primary\s+)?account\s*(?:number|#|no\.?|num\.?)\s*[:\-]?\s*([\d\-]{4,20})',
        r'(?i)acct\.?\s*(?:#|no\.?)?\s*[:\-]?\s*([\dX\*\•\-]{6,20})',
        r'(?i)account\s*ending\s+(?:in\s+)?(\d{4})',
        r'(?i)account\s+number[:\s]+[•\*x\-]{0,8}\s*(\d{4,17})',
        r'(?<!\d)([\*•\.]{3,}\s*\d{4})(?!\d)',
    ]
    for pat in acct_patterns:
        m = re.search(pat, t)
        if m:
            result["account_number"] = m.group(1).strip()
            break

    # ── Statement period ─────────────────────────────────────────────────────
    date_re = r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
    period_m = None

    # Try all common period formats in one pass
    period_patterns = [
        r'(?i)(?:statement\s*period|period\s*covered|billing\s*period|for\s+the\s+period|cycle)\s*[:\-]?\s*' + date_re + r'\s*(?:through|thru|to|\-|–)\s*' + date_re,
        date_re + r'\s*(?:through|thru)\s*' + date_re,
        r'(?i)from\s+' + date_re + r'\s+to\s+' + date_re,
    ]
    for pat in period_patterns:
        period_m = re.search(pat, t)
        if period_m:
            break

    if period_m:
        result["period_start"] = period_m.group(1)
        result["period_end"]   = period_m.group(2)
        try:
            from datetime import datetime as _dt
            for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y"):
                try:
                    dt = _dt.strptime(period_m.group(2), fmt)
                    result["statement_month"] = dt.strftime("%B %Y")
                    break
                except ValueError:
                    continue
        except Exception:
            result["statement_month"] = period_m.group(2)
    else:
        month_m = re.search(
            r'(?i)(January|February|March|April|May|June|July|August|'
            r'September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
            r'\.?\s+(\d{4})',
            t
        )
        if month_m:
            result["statement_month"] = f"{month_m.group(1)} {month_m.group(2)}"

    # ── Balances ─────────────────────────────────────────────────────────────
    # Strategy A: PNC/multi-column "Balance Summary" table
    # Labels split across lines, all values on one row: "26.83 6,654.10 6,298.81 382.12"
    for i, line in enumerate(lines):
        if re.search(r'(?i)balance\s*summary', line):
            for j in range(1, 25):
                if i + j >= len(lines):
                    break
                nums = _dollars_on_line(lines[i + j])
                if len(nums) >= 3:
                    # PNC order: beginning, deposits, deductions, ending
                    result["beginning_balance"] = nums[0]
                    if len(nums) > 1: result["deposits_total"]    = nums[1]
                    if len(nums) > 2: result["withdrawals_total"] = nums[2]
                    if len(nums) > 3: result["ending_balance"]    = nums[3]
                    break
            break

    # Strategy B: inline label + amount (Chase, BofA, Wells)
    if not result["beginning_balance"]:
        result["beginning_balance"] = _first_dollar_after(
            r'(?:beginning|opening|start(?:ing)?|prior|previous)\s*(?:statement\s*)?balance', t, 80
        )
    if not result["ending_balance"]:
        result["ending_balance"] = _first_dollar_after(
            r'(?:ending|closing|end(?:ing)?|new|current)\s*(?:statement\s*)?balance', t, 80
        )
    if not result["lowest_balance"]:
        result["lowest_balance"] = _first_dollar_after(
            r'(?:low(?:est)?|minimum|min\.?)\s*(?:daily\s*)?balance', t, 80
        )
    if not result["deposits_total"]:
        result["deposits_total"] = _first_dollar_after(
            r'(?:total\s+)?(?:deposits?\s+and\s+(?:other\s+)?additions?|deposits?\s+total|total\s+(?:deposits?|credits?))', t, 120
        )
    if not result["withdrawals_total"]:
        result["withdrawals_total"] = _first_dollar_after(
            r'(?:total\s+)?(?:checks?\s+and\s+(?:other\s+)?deductions?|withdrawals?\s+total|total\s+(?:withdrawals?|debits?))', t, 120
        )

    # Strategy C: "totaling $X" pattern
    if not result["deposits_total"]:
        m = re.search(r'(?i)(?:deposits?|additions?)\s+totaling\s+\$?([\d,]+\.\d{2})', t)
        if m: result["deposits_total"] = m.group(1).replace(",", "")
    if not result["withdrawals_total"]:
        m = re.search(r'(?i)(?:withdrawals?|deductions?|checks?)\s+totaling\s+\$?([\d,]+\.\d{2})', t)
        if m: result["withdrawals_total"] = m.group(1).replace(",", "")

    return result


def cross_reference_approval(bank_text: str, approval_notes: str) -> list:
    """
    Given bank statement text and freeform approval condition notes,
    look for dollar amounts and payees mentioned in the approval notes
    inside the bank statement. Returns a list of match result dicts.
    """
    results = []
    if not approval_notes.strip():
        return results

    # Extract dollar amounts from approval notes
    amounts = re.findall(r'\$\s*([\d,]+(?:\.\d{2})?)', approval_notes)
    for amt_str in amounts:
        amt_clean = amt_str.replace(",", "")
        # Search bank text for same amount
        pattern = re.escape(amt_str.replace(",", "")) + r'|' + re.escape(amt_str)
        found = bool(re.search(pattern, bank_text))
        results.append({
            "type":  "amount",
            "query": f"${amt_str}",
            "found": found,
            "note":  f"Amount ${amt_str} {'found in statement' if found else 'NOT found in statement'}",
        })

    # Extract payee/company names from approval notes (capitalized words 3+ chars)
    payees = re.findall(r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){0,3})\b', approval_notes)
    # Deduplicate and filter common words
    skip = {"The", "And", "For", "With", "From", "That", "This", "Per", "Any",
            "All", "Bank", "Loan", "Must", "Will", "See", "Also"}
    seen = set()
    for payee in payees:
        if payee in skip or payee in seen:
            continue
        seen.add(payee)
        found = bool(re.search(re.escape(payee), bank_text, re.IGNORECASE))
        results.append({
            "type":  "payee",
            "query": payee,
            "found": found,
            "note":  f"'{payee}' {'found in statement' if found else 'not found in statement'}",
        })

    return results


# ---------------------------------------------------------------------------
# Bank Statement Analysis (50-rule offline check)
# ---------------------------------------------------------------------------

def check_bank_rules(pdf_text: str, user_history=None) -> str:
    """
    Bank statement analysis — 50 rules, three types:
      REQUIRED  — must be present; MISSING = problem
      FLAG      — must NOT be present; FOUND = problem
      INFO      — optional; only surfaces if found (sourcing may be needed)
    """
    t = pdf_text
    results = []
    ok_count = flag_count = missing_count = info_count = 0

    # Each rule: (num, type, label, pattern, ok_msg, bad_msg)
    # type: "required" | "flag" | "info"
    rules = [
        # ── Identity & structure ──────────────────────────────────────────────
        (1,  "required", "Ending balance present",
         r'(?i)(?:ending|closing)\s*balance',
         "Ending / closing balance found on statement.",
         "Ending balance not found — verify all pages are present."),

        (2,  "required", "Statement period shown",
         r'(?i)(?:statement\s*period|from.*through|beginning.*ending|\d{1,2}/\d{1,2}/\d{2,4}.*\d{1,2}/\d{1,2}/\d{2,4})',
         "Statement period dates found.",
         "Statement period dates not found — confirm coverage window."),

        (8,  "required", "All pages present (page X of Y)",
         r'(?i)page\s*\d+\s*(?:of|/)\s*\d+',
         "Page numbering found (e.g. Page 1 of 3).",
         "Page count not found — confirm no pages are missing."),

        (11, "required", "Statement date is recent (2020+)",
         r'(?i)\b20(2[0-9])\b',
         "Recent year found on statement.",
         "Could not confirm statement year — verify date is within required window."),

        (12, "required", "Account number present",
         r'(?i)account\s*(?:number|#|no\.?)\s*:?\s*[\dX\*]+',
         "Account number found on statement.",
         "Account number not found — statement may be incomplete."),

        (14, "required", "Bank name / institution present",
         r'(?i)(?:bank|credit\s*union|financial|savings|N\.?A\.|F\.?S\.?B\.?)',
         "Bank / institution name found.",
         "Bank name not detected — verify source institution is identified."),

        (29, "required", "Account type identified (checking/savings)",
         r'(?i)(?:checking|savings|money\s*market|share\s*draft)',
         "Account type found (checking / savings / money market).",
         "Account type not identified — confirm this is a deposit account statement."),

        (31, "required", "Opening / beginning balance present",
         r'(?i)(?:opening|beginning)\s*balance',
         "Opening balance found.",
         "Opening balance not found — verify first statement page is included."),

        (36, "required", "Statement period dates shown",
         r'(?i)(?:period|from|through|beginning|ending)\s*:?\s*\d',
         "Period start/end dates found.",
         "Period dates not clearly labeled — cross-check cover page."),

        (41, "required", "Currency is USD",
         r'(?i)(?:USD|\$)',
         "USD / dollar symbol found — domestic account confirmed.",
         "No USD indicator found — confirm this is a U.S. account."),

        # ── Income verification ───────────────────────────────────────────────
        (4,  "required", "Deposit activity present",
         r'(?i)deposit|credit',
         "Deposit / credit activity found.",
         "No deposit or credit activity detected — statement may be empty or scanned."),

        (6,  "required", "Direct deposit or ACH present",
         r'(?i)(?:direct\s*deposit|ACH|payroll)',
         "Direct deposit / ACH / payroll found.",
         "No direct deposit or ACH detected — income sourcing may be needed."),

        (20, "required", "Payroll / income entries present",
         r'(?i)payroll|direct\s*deposit|ACH|salary|wages',
         "Payroll / income transactions found.",
         "No payroll entries found — confirm income source with VOE or pay stubs."),

        (43, "required", "Income source consistent",
         r'(?i)(?:payroll|direct\s*deposit|ACH|salary)',
         "Income source entries are present.",
         "Income source not clearly identified in statement."),

        (44, "required", "Normal expense activity present",
         r'(?i)(?:payment|purchase|debit|withdrawal)',
         "Normal debit / expense activity found.",
         "No expense activity detected — may indicate incomplete statement."),

        (19, "info", "Rent or mortgage payment",
         r'(?i)(?:rent|mortgage|housing)\s*(?:payment)?',
         "Rent or mortgage payment found — document housing history.",
         None),

        (16, "info", "Average daily balance shown",
         r'(?i)average\s*(?:daily)?\s*balance',
         "Average daily balance figure found on statement.",
         None),

        # ── Red flags ─────────────────────────────────────────────────────────
        (3,  "flag", "Overdraft / OD fees",
         r'(?i)overdraft|OD\s*fee|insufficient\s*fund',
         "No overdraft or OD fee language found.",
         "Overdraft / OD fee language detected — document and explain."),

        (15, "flag", "NSF fees",
         r'(?i)NSF|non[\s-]*sufficient\s*fund|returned\s*item',
         "No NSF fee language found.",
         "NSF / non-sufficient funds language detected — review and explain."),

        (34, "flag", "Returned deposits",
         r'(?i)return(?:ed)?\s*(?:deposit|item|check)',
         "No returned deposit language found.",
         "Returned deposit / item detected — review transaction detail."),

        (35, "flag", "Stop payments",
         r'(?i)stop\s*payment',
         "No stop-payment entries found.",
         "Stop payment detected — obtain explanation from borrower."),

        (10, "flag", "Negative balance",
         r'(?i)(?:negative\s*balance|\-\s*\$\s*\d)',
         "No negative balance detected.",
         "Negative balance language found — review account history."),

        (7,  "flag", "Account freeze / hold / restriction",
         r'(?i)(?:freeze|account\s*hold|restrict(?:ed)?|suspend(?:ed)?)',
         "No account freeze or restriction language found.",
         "Account freeze / hold / restriction language detected — borrower must explain."),

        (17, "flag", "Unexplained wire transfers",
         r'(?i)wire\s*(?:transfer|out|in)',
         "No wire transfer language found.",
         "Wire transfer detected — source funds and obtain explanation letter if > 50% monthly income."),

        (18, "flag", "Cash advances",
         r'(?i)cash\s*advance',
         "No cash advance entries found.",
         "Cash advance detected — may indicate undisclosed liability; review."),

        (21, "flag", "Gambling transactions",
         r'(?i)(?:casino|gambl(?:ing)?|lottery|poker|bet(?:ting)?|wager)',
         "No gambling transactions found.",
         "Gambling transaction language detected — review frequency and amounts."),

        (22, "flag", "Crypto transactions",
         r'(?i)(?:coinbase|binance|crypto(?:currency)?|bitcoin|ethereum|blockchain)',
         "No crypto transaction language found.",
         "Crypto platform transaction detected — source and document if large."),

        (28, "flag", "Foreign currency / exchange",
         r'(?i)(?:foreign\s*currency|currency\s*exchange|forex|\bFX\b)',
         "No foreign currency exchange found.",
         "Foreign currency exchange detected — verify account is domestic."),

        (33, "flag", "Charge-off notices",
         r'(?i)charge[\s-]*off',
         "No charge-off notices found.",
         "Charge-off language detected — confirm this does not affect the loan."),

        (40, "flag", "Redacted or obscured information",
         r'(?i)(?:redact|black[\s-]*out|XXXX|censored)',
         "No redacted information detected.",
         "Redacted / XXXX content detected — obtain unredacted statement."),

        (42, "flag", "High-risk merchants (payday, pawn, casino)",
         r'(?i)(?:payday\s*loan|pawn|title\s*loan|check\s*(?:cash|advance))',
         "No high-risk merchant transactions found.",
         "High-risk merchant transaction detected — review and document."),

        (47, "flag", "Bankruptcy-related transactions",
         r'(?i)(?:trustee|bankruptcy|chapter\s*(?:7|11|13))',
         "No bankruptcy-related transactions found.",
         "Bankruptcy-related transaction detected — verify discharge status and lender eligibility."),

        (45, "flag", "Undisclosed loan payments",
         r'(?i)(?:loan\s*payment|installment|note\s*payment)',
         "No undisclosed loan payment entries found.",
         "Loan / installment payment detected — confirm all liabilities are on the 1003."),

        # ── Optional / informational ──────────────────────────────────────────
        (5,  "info", "Large deposits (>$1,000)",
         r'(?i)(?:deposit|credit).*\$\s*[1-9]\d{3,}|\$\s*[1-9]\d{3,}.*(?:deposit|credit)',
         "Large deposit(s) detected — may require sourcing letter if >50% of monthly income.",
         None),

        (23, "info", "Tax refund / IRS deposit",
         r'(?i)(?:tax\s*refund|IRS|U\.?S\.?\s*Treasury)',
         "Tax refund / IRS deposit found — document source.",
         None),

        (24, "info", "Child support payments",
         r'(?i)child\s*support',
         "Child support found — if income, verify court order and 3-year continuance.",
         None),

        (25, "info", "Social Security / pension / retirement",
         r'(?i)(?:social\s*security|SSI|SSA|pension|retirement)',
         "SSI / pension / retirement income found — document award letter.",
         None),

        (26, "info", "Dividend or investment income",
         r'(?i)(?:dividend|investment\s*(?:income|return))',
         "Dividend / investment income found — 2-year average may be required.",
         None),

        (27, "info", "Interest earned",
         r'(?i)interest\s*(?:earned|paid|credit)',
         "Interest income found on statement.",
         None),

        (30, "info", "Joint account holder",
         r'(?i)(?:joint\s*account|\band\b\s+[A-Z][a-z]+\s+[A-Z][a-z]+)',
         "Joint account holder may be present — verify name matches borrower.",
         None),

        (46, "info", "Transfer to savings / savings deposits",
         r'(?i)(?:transfer\s*to\s*savings|savings\s*deposit)',
         "Savings transfers found — supports reserves documentation.",
         None),

        # ── Cannot determine from text ────────────────────────────────────────
        (9,  "manual", "Account holder name matches borrower", None, None, None),
        (13, "manual", "Borrower name consistent across all pages", None, None, None),
        (38, "manual", "No handwritten alterations", None, None, None),
        (39, "manual", "Document appears digitally generated (not photographed)", None, None, None),
        (48, "manual", "Account seasoning (established >60 days)", None, None, None),
        (49, "manual", "No dormant periods (60+ days with no activity)", None, None, None),
        (50, "manual", "Overall balance trend is stable or increasing", None, None, None),
    ]

    lines_required = []
    lines_flag = []
    lines_info = []
    lines_manual = []

    for num, rtype, label, pattern, ok_msg, bad_msg in rules:
        if rtype == "manual":
            lines_manual.append(f"MANUAL|{num}|{label}")
            continue

        matched = bool(pattern and re.search(pattern, t))

        if rtype == "required":
            if matched:
                lines_required.append(f"OK|{num}|{label}|{ok_msg}")
                ok_count += 1
            else:
                lines_required.append(f"MISSING|{num}|{label}|{bad_msg}")
                missing_count += 1

        elif rtype == "flag":
            if matched:
                lines_flag.append(f"FLAG|{num}|{label}|{bad_msg}")
                flag_count += 1
            else:
                lines_flag.append(f"OK|{num}|{label}|{ok_msg}")
                ok_count += 1

        elif rtype == "info":
            if matched:
                lines_info.append(f"INFO|{num}|{label}|{ok_msg}")
                info_count += 1
            # Not found = irrelevant to this borrower, skip

    # Build output string — sections separated by a divider the UI can key on
    output_lines = []

    output_lines.append(f"SUMMARY|{ok_count}|{flag_count}|{missing_count}|{info_count}")

    output_lines.append("SECTION|Required Checks")
    output_lines.extend(lines_required)

    output_lines.append("SECTION|Red Flags")
    output_lines.extend(lines_flag)

    if lines_info:
        output_lines.append("SECTION|Items Found — May Need Documentation")
        output_lines.extend(lines_info)

    output_lines.append("SECTION|Manual Review Required")
    output_lines.extend(lines_manual)

    return "\n".join(output_lines)


# ---------------------------------------------------------------------------
# Risk Flags (offline pattern scan)
# ---------------------------------------------------------------------------

def flag_risks(pdf_text: str, user_history=None) -> str:
    """Scan for risk indicators using regex."""
    flags = []
    t = pdf_text

    # DTI
    dti_match = re.search(r'(?i)(?:DTI|debt[\s-]*to[\s-]*income)\s*[:\s]*(\d+\.?\d*)\s*%', t)
    if dti_match:
        dti = float(dti_match.group(1))
        if dti > 50:
            flags.append(f"**DTI:** {dti}% - **Severity:** HIGH - Exceeds all standard limits. May need manual downgrade or denial.")
        elif dti > 45:
            flags.append(f"**DTI:** {dti}% - **Severity:** HIGH - Above 45% threshold. Needs strong compensating factors.")
        elif dti > 43:
            flags.append(f"**DTI:** {dti}% - **Severity:** MEDIUM - Above QM limit of 43%. Check for exceptions/AUS approval.")
        else:
            flags.append(f"**DTI:** {dti}% - within acceptable range.")

    # Credit Score
    fico_matches = re.findall(r'\b([3-8]\d{2})\b', t)
    fico_scores = [int(s) for s in fico_matches if 300 <= int(s) <= 850]
    if fico_scores:
        low = min(fico_scores)
        if low < 580:
            flags.append(f"**Credit Score:** {low} detected - **Severity:** HIGH - Below FHA minimum. Very limited options.")
        elif low < 620:
            flags.append(f"**Credit Score:** {low} detected - **Severity:** HIGH - Subprime range. FHA only with 10% down.")
        elif low < 680:
            flags.append(f"**Credit Score:** {low} detected - **Severity:** MEDIUM - May affect rate/PMI pricing.")

    # LTV
    ltv_match = re.search(r'(?i)(?:LTV|loan[\s-]*to[\s-]*value)\s*[:\s]*(\d+\.?\d*)\s*%', t)
    if ltv_match:
        ltv = float(ltv_match.group(1))
        if ltv > 97:
            flags.append(f"**LTV:** {ltv}% - **Severity:** HIGH - Exceeds most program limits.")
        elif ltv > 95:
            flags.append(f"**LTV:** {ltv}% - **Severity:** MEDIUM - High LTV. Check program eligibility.")
        elif ltv > 90:
            flags.append(f"**LTV:** {ltv}% - **Severity:** LOW - PMI required (conventional).")

    # Income red flags
    if re.search(r'(?i)(?:gap\s*in\s*employ|unemploy|laid\s*off|terminated)', t):
        flags.append("**Income:** Employment gap detected - **Severity:** MEDIUM - Need LOE (letter of explanation).")
    if re.search(r'(?i)(?:declining\s*income|decrease\s*in)', t):
        flags.append("**Income:** Declining income trend - **Severity:** MEDIUM - May affect qualifying income calc.")

    # Asset red flags
    if re.search(r'(?i)(?:large\s*deposit|unexplained\s*deposit|source\s*of\s*funds)', t):
        flags.append("**Assets:** Large/unexplained deposit reference - **Severity:** MEDIUM - Need source documentation.")
    if re.search(r'(?i)(?:gift\s*fund|gift\s*letter)', t):
        flags.append("**Assets:** Gift funds referenced - **Severity:** LOW - Ensure gift letter + donor bank statement present.")
    if re.search(r'(?i)(?:borrowed\s*(?:fund|down)|loan.*(?:down\s*payment|closing))', t):
        flags.append("**Assets:** Borrowed funds for closing - **Severity:** HIGH - Must meet program guidelines.")

    # Property red flags
    if re.search(r'(?i)(?:flood\s*zone\s*(?:A|AE|V|VE))', t):
        flags.append("**Property:** Flood zone A/V detected - **Severity:** MEDIUM - Flood insurance required.")
    if re.search(r'(?i)(?:apprais.*(?:below|under|short|less\s*than)|value\s*(?:concern|issue))', t):
        flags.append("**Property:** Appraisal concern detected - **Severity:** HIGH - May affect LTV and loan amount.")
    if re.search(r'(?i)(?:title\s*(?:issue|defect|exception|lien)|mechanic.*lien|judgment)', t):
        flags.append("**Property:** Title issue detected - **Severity:** HIGH - Must be resolved before closing.")

    # Compliance
    if re.search(r'(?i)(?:TRID|RESPA)\s*(?:violation|issue|concern)', t):
        flags.append("**Compliance:** TRID/RESPA concern - **Severity:** HIGH - Review timing and disclosure requirements.")
    if re.search(r'(?i)(?:missing\s*(?:disclosure|signature)|unsigned)', t):
        flags.append("**Compliance:** Missing disclosure/signature - **Severity:** MEDIUM - Need before closing.")

    if not flags:
        return "No significant risk flags detected in this document.\n\n*Note: Offline pattern scan - manual review recommended.*"

    return "\n\n".join(f"* {f}" for f in flags) + "\n\n*Note: Offline risk scan based on keyword detection. Always verify manually.*"


# ---------------------------------------------------------------------------
# Email Drafting (template-based, no AI)
# ---------------------------------------------------------------------------

_EMAIL_TEMPLATES = {
    "Borrower": {
        "English": (
            "Subject: Action Required - Outstanding Loan Conditions\n\n"
            "Dear Borrower,\n\n"
            "We are working to move your loan toward closing as quickly as possible. "
            "To keep things on track, we need the following item(s) from you:\n\n"
            "{conditions}\n\n"
            "Please provide these at your earliest convenience. If you have any questions "
            "about any of these items, don't hesitate to reach out.\n\n"
            "Thank you for your prompt attention to this matter.\n\n"
            "Best regards,\n[Your Name]\nLoan Processor"
        ),
        "Spanish": (
            "Asunto: Accion Requerida - Condiciones Pendientes del Prestamo\n\n"
            "Estimado/a Prestatario/a,\n\n"
            "Estamos trabajando para avanzar su prestamo hacia el cierre lo mas rapido posible. "
            "Para mantener todo en orden, necesitamos los siguientes documentos de su parte:\n\n"
            "{conditions}\n\n"
            "Por favor proporcionelos lo antes posible. Si tiene alguna pregunta "
            "sobre cualquiera de estos documentos, no dude en comunicarse con nosotros.\n\n"
            "Gracias por su pronta atencion a este asunto.\n\n"
            "Atentamente,\n[Su Nombre]\nProcesador de Prestamos"
        ),
    },
    "Title": {
        "English": (
            "Subject: Outstanding Title Conditions - Loan File\n\n"
            "Dear Title Team,\n\n"
            "We have the following outstanding conditions related to title for the above-referenced loan:\n\n"
            "{conditions}\n\n"
            "Please provide these items at your earliest convenience so we can proceed toward closing.\n\n"
            "Thank you,\n[Your Name]\nLoan Processor"
        ),
        "Spanish": (
            "Asunto: Condiciones Pendientes de Titulo - Expediente de Prestamo\n\n"
            "Estimado Equipo de Titulo,\n\n"
            "Tenemos las siguientes condiciones pendientes relacionadas con el titulo para el prestamo mencionado:\n\n"
            "{conditions}\n\n"
            "Por favor proporcionelos lo antes posible para que podamos proceder hacia el cierre.\n\n"
            "Gracias,\n[Su Nombre]\nProcesador de Prestamos"
        ),
    },
    "Underwriter": {
        "English": (
            "Subject: Condition Response / Documentation Submission\n\n"
            "Dear Underwriter,\n\n"
            "Please find the following items submitted in response to outstanding conditions:\n\n"
            "{conditions}\n\n"
            "Please review and advise if any additional documentation is needed.\n\n"
            "Thank you,\n[Your Name]\nLoan Processor"
        ),
        "Spanish": (
            "Asunto: Respuesta a Condiciones / Envio de Documentacion\n\n"
            "Estimado/a Suscriptor/a,\n\n"
            "Adjunto los siguientes documentos en respuesta a las condiciones pendientes:\n\n"
            "{conditions}\n\n"
            "Por favor revise e indique si se necesita documentacion adicional.\n\n"
            "Gracias,\n[Su Nombre]\nProcesador de Prestamos"
        ),
    },
    "Insurance": {
        "English": (
            "Subject: Insurance Documentation Needed - Loan File\n\n"
            "Dear Insurance Agent,\n\n"
            "We need the following insurance-related item(s) for the above-referenced loan:\n\n"
            "{conditions}\n\n"
            "Please provide at your earliest convenience.\n\n"
            "Thank you,\n[Your Name]\nLoan Processor"
        ),
        "Spanish": (
            "Asunto: Documentacion de Seguro Necesaria - Expediente de Prestamo\n\n"
            "Estimado/a Agente de Seguros,\n\n"
            "Necesitamos los siguientes documentos relacionados con el seguro para el prestamo mencionado:\n\n"
            "{conditions}\n\n"
            "Por favor proporcionelos lo antes posible.\n\n"
            "Gracias,\n[Su Nombre]\nProcesador de Prestamos"
        ),
    },
    "Appraiser": {
        "English": (
            "Subject: Appraisal Condition Follow-Up\n\n"
            "Dear Appraiser,\n\n"
            "The following appraisal-related condition(s) are outstanding:\n\n"
            "{conditions}\n\n"
            "Please advise on timeline for completion.\n\n"
            "Thank you,\n[Your Name]\nLoan Processor"
        ),
        "Spanish": (
            "Asunto: Seguimiento de Condiciones de Avaluo\n\n"
            "Estimado/a Tasador/a,\n\n"
            "Las siguientes condiciones relacionadas con el avaluo estan pendientes:\n\n"
            "{conditions}\n\n"
            "Por favor indique el tiempo estimado para su finalizacion.\n\n"
            "Gracias,\n[Su Nombre]\nProcesador de Prestamos"
        ),
    },
    "Co-Borrower": {
        "English": (
            "Subject: Action Required - Outstanding Loan Conditions\n\n"
            "Dear Co-Borrower,\n\n"
            "To keep your loan moving toward closing, we need the following item(s) from you:\n\n"
            "{conditions}\n\n"
            "Please provide at your earliest convenience.\n\n"
            "Thank you,\n[Your Name]\nLoan Processor"
        ),
        "Spanish": (
            "Asunto: Accion Requerida - Condiciones Pendientes del Prestamo\n\n"
            "Estimado/a Co-Prestatario/a,\n\n"
            "Para mantener su prestamo avanzando hacia el cierre, necesitamos lo siguiente de su parte:\n\n"
            "{conditions}\n\n"
            "Por favor proporcionelo lo antes posible.\n\n"
            "Gracias,\n[Su Nombre]\nProcesador de Prestamos"
        ),
    },
    "Realtor": {
        "English": (
            "Subject: Outstanding Items - Loan File\n\n"
            "Hello,\n\n"
            "We have the following outstanding item(s) for your buyer's loan file:\n\n"
            "{conditions}\n\n"
            "Please assist in obtaining these as soon as possible.\n\n"
            "Thank you,\n[Your Name]\nLoan Processor"
        ),
        "Spanish": (
            "Asunto: Documentos Pendientes - Expediente de Prestamo\n\n"
            "Hola,\n\n"
            "Tenemos los siguientes documentos pendientes para el expediente de prestamo de su comprador:\n\n"
            "{conditions}\n\n"
            "Por favor ayudenos a obtenerlos lo antes posible.\n\n"
            "Gracias,\n[Su Nombre]\nProcesador de Prestamos"
        ),
    },
    "Seller": {
        "English": (
            "Subject: Seller Documentation Needed\n\n"
            "Dear Seller,\n\n"
            "We need the following item(s) from the seller to proceed with closing:\n\n"
            "{conditions}\n\n"
            "Please provide at your earliest convenience.\n\n"
            "Thank you,\n[Your Name]\nLoan Processor"
        ),
        "Spanish": (
            "Asunto: Documentacion del Vendedor Necesaria\n\n"
            "Estimado/a Vendedor/a,\n\n"
            "Necesitamos los siguientes documentos del vendedor para proceder con el cierre:\n\n"
            "{conditions}\n\n"
            "Por favor proporcionelos lo antes posible.\n\n"
            "Gracias,\n[Su Nombre]\nProcesador de Prestamos"
        ),
    },
    "Loan Officer": {
        "English": (
            "Subject: Loan File Update - Action Needed\n\n"
            "Hi,\n\n"
            "The following item(s) on this loan need your attention:\n\n"
            "{conditions}\n\n"
            "Please advise on next steps.\n\n"
            "Thanks,\n[Your Name]\nLoan Processor"
        ),
        "Spanish": (
            "Asunto: Actualizacion del Expediente - Accion Necesaria\n\n"
            "Hola,\n\n"
            "Los siguientes documentos de este prestamo necesitan su atencion:\n\n"
            "{conditions}\n\n"
            "Por favor indique los siguientes pasos.\n\n"
            "Gracias,\n[Su Nombre]\nProcesador de Prestamos"
        ),
    },
    "Closer": {
        "English": (
            "Subject: Closing Conditions - Loan File\n\n"
            "Dear Closer,\n\n"
            "The following closing-related item(s) are outstanding:\n\n"
            "{conditions}\n\n"
            "Please advise when we can schedule closing.\n\n"
            "Thank you,\n[Your Name]\nLoan Processor"
        ),
        "Spanish": (
            "Asunto: Condiciones de Cierre - Expediente de Prestamo\n\n"
            "Estimado/a Cerrador/a,\n\n"
            "Los siguientes documentos relacionados con el cierre estan pendientes:\n\n"
            "{conditions}\n\n"
            "Por favor indique cuando podemos programar el cierre.\n\n"
            "Gracias,\n[Su Nombre]\nProcesador de Prestamos"
        ),
    },
    "Employer": {
        "English": (
            "Subject: Verification of Employment Request\n\n"
            "To Whom It May Concern,\n\n"
            "We are processing a mortgage application and need the following from the employer:\n\n"
            "{conditions}\n\n"
            "Please return at your earliest convenience.\n\n"
            "Thank you,\n[Your Name]\nLoan Processor"
        ),
        "Spanish": (
            "Asunto: Solicitud de Verificacion de Empleo\n\n"
            "A quien corresponda,\n\n"
            "Estamos procesando una solicitud de hipoteca y necesitamos lo siguiente del empleador:\n\n"
            "{conditions}\n\n"
            "Por favor devuelvalo lo antes posible.\n\n"
            "Gracias,\n[Su Nombre]\nProcesador de Prestamos"
        ),
    },
    "Jr Underwriter": {
        "English": (
            "Subject: Condition Response / Documentation Submission\n\n"
            "Hi,\n\n"
            "Please find the following items submitted in response to outstanding conditions:\n\n"
            "{conditions}\n\n"
            "Let me know if anything else is needed.\n\n"
            "Thanks,\n[Your Name]\nLoan Processor"
        ),
        "Spanish": (
            "Asunto: Respuesta a Condiciones / Envio de Documentacion\n\n"
            "Hola,\n\n"
            "Adjunto los siguientes documentos en respuesta a las condiciones pendientes:\n\n"
            "{conditions}\n\n"
            "Avisame si algo mas es necesario.\n\n"
            "Gracias,\n[Su Nombre]\nProcesador de Prestamos"
        ),
    },
    "Manager": {
        "English": (
            "Subject: Loan File - Escalation\n\n"
            "Hi,\n\n"
            "The following item(s) on this loan need manager review:\n\n"
            "{conditions}\n\n"
            "Please advise.\n\n"
            "Thanks,\n[Your Name]\nLoan Processor"
        ),
        "Spanish": (
            "Asunto: Expediente de Prestamo - Escalacion\n\n"
            "Hola,\n\n"
            "Los siguientes documentos de este prestamo requieren revision del gerente:\n\n"
            "{conditions}\n\n"
            "Por favor indique.\n\n"
            "Gracias,\n[Su Nombre]\nProcesador de Prestamos"
        ),
    },
}


def draft_email(conditions: str, recipient_type: str, language: str = "English", user_history=None) -> str:
    """Draft an email from templates. No AI needed."""
    templates = _EMAIL_TEMPLATES.get(recipient_type, _EMAIL_TEMPLATES.get("Borrower"))
    template = templates.get(language, templates.get("English", ""))
    if not template:
        template = _EMAIL_TEMPLATES["Borrower"]["English"]
    # Safe substitution — avoids crash when condition text contains { } characters
    return template.replace("{conditions}", conditions)


def auto_draft_emails(conditions: str, user_history=None) -> str:
    """Auto-draft all emails grouped by responsible party."""
    # Parse conditions table to group by party
    parties = {}
    for line in conditions.split("\n"):
        if line.strip().startswith("|") and not line.strip().startswith("| #") and "---" not in line:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) >= 4:
                party = cells[2]
                desc = f"- #{cells[0]}: {cells[1]} ({cells[3]})"
                parties.setdefault(party, []).append(desc)

    if not parties:
        return "No conditions found to draft emails for."

    output = []
    for party, items in parties.items():
        cond_text = "\n".join(items)
        email = draft_email(cond_text, party, "English")
        output.append(f"---\n**TO: {party}**\n\n{email}")

        # Spanish version for borrower
        if party == "Borrower":
            email_es = draft_email(cond_text, party, "Spanish")
            output.append(f"---\n**TO: Borrower (Spanish)**\n\n{email_es}")

    return "\n\n".join(output)


# ---------------------------------------------------------------------------
# Web Research (offline - just provides search links, no actual web calls)
# ---------------------------------------------------------------------------

_RESEARCH_LINKS = {
    "business": "State Secretary of State website for your state",
    "flood": "https://msc.fema.gov/portal/search",
    "fha": "https://entp.hud.gov/clas/",
    "nmls": "https://www.nmlsconsumeraccess.org/",
    "property": "County assessor/recorder website for the property county",
    "hoa": "Property management company website (check HOA docs for contact)",
    "insurance": "Contact insurance carrier directly",
    "title": "State department of insurance website",
}


def web_research(conditions: str, user_history=None) -> str:
    """Suggest research links based on conditions. No web calls made."""
    suggestions = []
    t = conditions.lower()

    checks = [
        ("flood", "Flood zone verification", _RESEARCH_LINKS["flood"]),
        ("fha", "FHA case number lookup", _RESEARCH_LINKS["fha"]),
        ("nmls", "NMLS license verification", _RESEARCH_LINKS["nmls"]),
        ("hoa", "HOA verification", _RESEARCH_LINKS["hoa"]),
        ("estoppel", "HOA estoppel verification", _RESEARCH_LINKS["hoa"]),
        ("insurance", "Insurance verification", _RESEARCH_LINKS["insurance"]),
        ("title", "Title verification", _RESEARCH_LINKS["title"]),
        ("business", "Business entity verification", _RESEARCH_LINKS["business"]),
        ("property", "Property records lookup", _RESEARCH_LINKS["property"]),
        ("apprais", "Appraisal data", _RESEARCH_LINKS["property"]),
        ("employ", "Employment verification", "Company website or LinkedIn"),
    ]

    num = 0
    for keyword, desc, url in checks:
        if keyword in t:
            num += 1
            suggestions.append(f"| {num} | {desc} | Search for relevant documentation | {url} |")

    if not suggestions:
        return "No conditions require online verification based on the scan results."

    header = "| # | Condition | What to Search | Where to Look |\n|---|-----------|---------------|---------------|\n"
    return header + "\n".join(suggestions) + "\n\n*Note: Open these links in your browser manually. This app does not make web calls.*"


# ---------------------------------------------------------------------------
# Contacts Extraction (regex from document text)
# ---------------------------------------------------------------------------

def extract_contacts(pdf_text: str, user_history=None) -> str:
    """Extract names, contacts, and loan details from document using regex."""
    t = pdf_text

    # Try to find borrower name
    borrower = "Not found"
    for pat in [r'(?i)borrower\s*(?:name)?\s*[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'(?i)applicant\s*[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'(?i)prepared\s+for\s*[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)']:
        m = re.search(pat, t)
        if m:
            borrower = m.group(1).strip()
            break

    # Co-borrower
    co_borrower = "Not found"
    m = re.search(r'(?i)co[\s-]*borrower\s*(?:name)?\s*[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)', t)
    if m:
        co_borrower = m.group(1).strip()

    # Phone numbers
    phones = re.findall(r'(?:\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})', t)
    phone = phones[0] if phones else "Not found"

    # Email addresses
    emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', t)
    email = emails[0] if emails else "Not found"

    # Loan number
    loan_num = "Not found"
    m = re.search(r'(?i)loan\s*(?:number|#|no\.?)\s*[:\s]*([A-Z0-9-]+)', t)
    if m:
        loan_num = m.group(1).strip()

    # Loan amount
    loan_amt = "Not found"
    m = re.search(r'(?i)loan\s*amount\s*[:\s]*\$?([\d,]+\.?\d*)', t)
    if m:
        loan_amt = f"${m.group(1)}"

    # Property address
    prop_addr = "Not found"
    m = re.search(r'(?i)(?:property|subject)\s*address\s*[:\s]*(.+?)(?:\n|$)', t)
    if m:
        prop_addr = m.group(1).strip()[:100]

    # Loan type
    loan_type = "Not determined"
    if re.search(r'(?i)\bFHA\b', t):
        loan_type = "FHA"
    elif re.search(r'(?i)\bVA\b', t):
        loan_type = "VA"
    elif re.search(r'(?i)\bUSDA\b', t):
        loan_type = "USDA"
    elif re.search(r'(?i)conventional', t):
        loan_type = "Conventional"

    # Interest rate
    rate = "Not found"
    m = re.search(r'(?i)(?:interest|note)\s*rate\s*[:\s]*(\d+\.?\d*)\s*%', t)
    if m:
        rate = f"{m.group(1)}%"

    output = f"""**BORROWER(S):**
| Name | Role | Phone | Email | Address |
|------|------|-------|-------|---------|
| {borrower} | Primary Borrower | {phone} | {email} | {prop_addr} |
| {co_borrower} | Co-Borrower | Not found | Not found | - |

**LOAN DETAILS:**
- Loan Number: {loan_num}
- Loan Amount: {loan_amt}
- Property Address: {prop_addr}
- Loan Type: {loan_type}
- Interest Rate: {rate}

*Note: Contact info extracted via pattern matching. Verify accuracy manually.*"""

    return output


# ---------------------------------------------------------------------------
# Stacking Order (checklist scan)
# ---------------------------------------------------------------------------

def generate_stacking_order(pdf_text: str, user_history=None) -> str:
    """Generate stacking order checklist by scanning for document references."""
    t = pdf_text.lower()

    def check(pattern):
        return "[x]" if re.search(pattern, t) else "[ ]"

    output = """**LOAN FILE STACKING ORDER**

**Section 1: Application & Disclosures**
- {s1_1} Uniform Residential Loan Application (1003)
- {s1_2} Loan Estimate (LE) - initial
- {s1_3} Loan Estimate (LE) - revised
- {s1_4} Closing Disclosure (CD)
- {s1_5} Intent to Proceed
- {s1_6} Right to Receive Appraisal
- {s1_7} Servicing Disclosure
- {s1_8} ECOA Notice
- {s1_9} Privacy Policy
- {s1_10} Patriot Act Disclosure

**Section 2: Credit & Income**
- {s2_1} Credit Report (tri-merge)
- {s2_2} Pay stubs (most recent 30 days)
- {s2_3} W-2s (2 years)
- {s2_4} Tax Returns (2 years) / 4506-C
- {s2_5} VOE (Verification of Employment)
- {s2_6} Self-employment docs (if applicable)

**Section 3: Assets**
- {s3_1} Bank Statements (2 months, all pages)
- {s3_2} Investment/retirement account statements
- {s3_3} Gift letter + donor bank statement (if applicable)
- {s3_4} Earnest money deposit verification

**Section 4: Property**
- {s4_1} Purchase Agreement / Sales Contract
- {s4_2} Appraisal Report
- {s4_3} Title Commitment / Preliminary Title Report
- {s4_4} Survey
- {s4_5} Homeowner's Insurance Binder
- {s4_6} Flood Certification
- {s4_7} HOA Docs (if applicable)

**Section 5: Government / Program Specific**
- {s5_1} FHA Case Number Assignment
- {s5_2} VA Certificate of Eligibility (COE)
- {s5_3} USDA Eligibility
- {s5_4} MI Certificate (PMI)

**Section 6: Closing**
- {s6_1} Approval / Commitment Letter
- {s6_2} Conditions list
- {s6_3} Clear to Close (CTC)
- {s6_4} Closing Instructions
- {s6_5} Final CD
- {s6_6} Note
- {s6_7} Deed of Trust / Mortgage
- {s6_8} Settlement Statement

*Items marked [x] were referenced in the document. [ ] = not detected. Manual review recommended.*
""".format(
        s1_1=check(r'1003|uniform\s*residential|loan\s*application'),
        s1_2=check(r'loan\s*estimate|initial\s*le\b'),
        s1_3=check(r'revis(?:ed)?\s*(?:loan\s*estimate|le\b)|revised\s*le'),
        s1_4=check(r'closing\s*disclosure|final\s*cd|\bCD\b'),
        s1_5=check(r'intent\s*to\s*proceed'),
        s1_6=check(r'right\s*to\s*receive\s*appraisal'),
        s1_7=check(r'servicing\s*disclosure'),
        s1_8=check(r'ecoa|equal\s*credit'),
        s1_9=check(r'privacy\s*(?:policy|notice)'),
        s1_10=check(r'patriot\s*act|CIP'),
        s2_1=check(r'credit\s*report|tri[\s-]*merge|fico'),
        s2_2=check(r'pay\s*stub'),
        s2_3=check(r'w[\s-]*2'),
        s2_4=check(r'tax\s*return|1040|4506'),
        s2_5=check(r'voe|verification\s*of\s*employ'),
        s2_6=check(r'self[\s-]*employ|1099|schedule\s*c'),
        s3_1=check(r'bank\s*statement'),
        s3_2=check(r'(?:investment|retirement|401k|ira)\s*(?:statement|account)'),
        s3_3=check(r'gift\s*(?:letter|fund)'),
        s3_4=check(r'earnest\s*money|deposit\s*verif'),
        s4_1=check(r'purchase\s*(?:agreement|contract)|sales\s*contract'),
        s4_2=check(r'appraisal\s*report'),
        s4_3=check(r'title\s*(?:commit|prelim|report)'),
        s4_4=check(r'survey'),
        s4_5=check(r'(?:homeowner|hazard|HO[\s-]*[36])\s*insurance'),
        s4_6=check(r'flood\s*(?:cert|determin|zone)'),
        s4_7=check(r'hoa|homeowner.*association|estoppel'),
        s5_1=check(r'fha\s*case'),
        s5_2=check(r'(?:va\s*)?certificate\s*of\s*eligibility|coe'),
        s5_3=check(r'usda\s*(?:eligib|rural)'),
        s5_4=check(r'(?:pmi|mortgage\s*insurance)\s*(?:cert|certificate)'),
        s6_1=check(r'approv(?:al|ed)|commitment\s*letter'),
        s6_2=check(r'condition\s*(?:list|s\b)|prior\s*to'),
        s6_3=check(r'clear\s*to\s*close|ctc'),
        s6_4=check(r'closing\s*instruction'),
        s6_5=check(r'final\s*(?:cd|closing\s*disclosure)'),
        s6_6=check(r'promissory\s*note|\bnote\b.*(?:sign|execut)'),
        s6_7=check(r'deed\s*of\s*trust|mortgage\s*(?:deed|instrument)'),
        s6_8=check(r'settlement\s*statement|alta|hud[\s-]*1'),
    )

    return output


# ---------------------------------------------------------------------------
# Mega Checklist (pattern-based 250-item scan)
# ---------------------------------------------------------------------------

def run_mega_checklist(pdf_text: str, user_history=None) -> str:
    """Run mega checklist scan. Returns summary of key findings to keep output manageable."""
    t = pdf_text.lower()

    # Auto-detect document type
    doc_type = "Unknown"
    confidence = "Low"
    type_checks = [
        ("1003 Application", r'(?:1003|uniform\s*residential\s*loan\s*application)', "High"),
        ("Approval Letter", r'(?:approv(?:al|ed)|commitment\s*letter|underwriting)', "High"),
        ("Closing Disclosure (CD)", r'(?:closing\s*disclosure)', "High"),
        ("Loan Estimate (LE)", r'(?:loan\s*estimate)', "High"),
        ("Credit Report", r'(?:credit\s*(?:report|score)|fico|tri[\s-]*merge)', "High"),
        ("Bank Statement", r'(?:bank\s*statement|account\s*(?:summary|activity))', "High"),
        ("Appraisal", r'(?:appraisal\s*report|appraised\s*value|comparable)', "High"),
    ]
    for name, pat, conf in type_checks:
        if re.search(pat, t):
            doc_type = name
            confidence = conf
            break

    # Run key sections as summary rather than all 250 items
    sections = {
        "Loan Type": [
            ("Conventional", r'conventional'),
            ("FHA", r'\bfha\b'),
            ("VA", r'\bva\b'),
            ("USDA", r'\busda\b'),
            ("Fixed rate", r'fixed\s*rate'),
            ("ARM", r'(?:adjustable|arm)\s*rate'),
        ],
        "Property": [
            ("Single family", r'(?:single\s*family|sfr|1[\s-]*unit)'),
            ("Condo", r'condo'),
            ("PUD", r'\bpud\b'),
            ("Multi-unit", r'(?:2[\s-]*unit|3[\s-]*unit|4[\s-]*unit|multi)'),
            ("Primary residence", r'(?:primary\s*residen|owner\s*occup)'),
            ("Investment", r'(?:investment|rental)\s*property'),
        ],
        "Borrower": [
            ("SSN present", r'(?:ssn|social\s*security|\d{3}[\s-]*\d{2}[\s-]*\d{4}|xxx)'),
            ("DOB present", r'(?:date\s*of\s*birth|dob|\d{2}/\d{2}/\d{4})'),
            ("Employment", r'(?:employ|employer|occupation)'),
            ("Income", r'(?:income|salary|wages|earn)'),
            ("Assets", r'(?:asset|bank|checking|savings|401k)'),
            ("Credit score", r'(?:credit\s*score|fico|\b[67]\d{2}\b)'),
        ],
        "Disclosures": [
            ("Loan Estimate", r'loan\s*estimate'),
            ("Closing Disclosure", r'closing\s*disclosure'),
            ("Intent to Proceed", r'intent\s*to\s*proceed'),
            ("ECOA", r'ecoa|equal\s*credit'),
            ("Privacy", r'privacy'),
            ("4506-C", r'4506'),
        ],
    }

    output = f"**Auto-Detected Document Type:** {doc_type}\n**Confidence:** {confidence}\n\n"
    output += "| # | Category | Item | Status | Note |\n"
    output += "|---|----------|------|--------|------|\n"

    num = 0
    for section, items in sections.items():
        for item_name, pattern in items:
            num += 1
            found = bool(re.search(pattern, t))
            status = "Found" if found else "Not Found"
            note = "Detected in document" if found else "Not detected - may not apply"
            output += f"| {num} | {section} | {item_name} | {status} | {note} |\n"
            time.sleep(0.02)  # micro-pause

    output += f"\n*Scanned {num} key items from mega checklist. Full 250-item scan available on demand.*\n"
    output += "*This is an offline pattern scan. Manual review recommended for accuracy.*"

    return output


# ---------------------------------------------------------------------------
# 1003 Application Parser
# ---------------------------------------------------------------------------

def extract_1003(text: str) -> dict:
    """
    Extract structured fields from a Uniform Residential Loan Application (1003).
    Returns a dict with borrower, co-borrower, employment, loan, and missing_required.
    100% offline — regex only.
    """
    import re

    def _find(patterns, default=""):
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
            if m:
                val = (m.group(1) if m.lastindex else m.group(0)).strip()
                val = re.sub(r'\s+', ' ', val)
                if val and len(val) > 1:
                    return val
        return default

    # ── Borrower ────────────────────────────────────────────────────────────
    borrower_name = _find([
        r"(?:Borrower'?s?\s*Name|Borrower\s*Name|I\.\s*BORROWER)[:\s]+([A-Z][a-zA-Z\-']+(?:\s+[A-Z][a-zA-Z\-']+){1,4})",
        r"(?:^|\n)\s*Borrower[:\s]+([A-Z][a-zA-Z\-']+(?:\s+[A-Z][a-zA-Z\-']+){1,4})",
        r"(?:Applicant|APPLICANT)[:\s]+([A-Z][a-zA-Z\-']+(?:\s+[A-Z][a-zA-Z\-']+){1,4})",
    ])
    co_borrower_name = _find([
        r"(?:Co-?Borrower'?s?\s*Name|CO-?BORROWER\s*NAME)[:\s]+([A-Z][a-zA-Z\-']+(?:\s+[A-Z][a-zA-Z\-']+){1,4})",
        r"(?:Co-?Applicant)[:\s]+([A-Z][a-zA-Z\-']+(?:\s+[A-Z][a-zA-Z\-']+){1,4})",
    ])

    # SSN — first match = borrower, second = co-borrower
    ssn_all = re.findall(r"\b(\d{3}[-\s]\d{2}[-\s]\d{4})\b", text)
    ssn = ssn_all[0] if ssn_all else _find([
        r"(?:Social\s*Security\s*(?:Number|No\.?|#)|SSN)[:\s#]*(\d{3}[-\s]\d{2}[-\s]\d{4})",
    ])
    co_ssn = ssn_all[1] if len(ssn_all) >= 2 else ""

    dob = _find([
        r"(?:Date\s*of\s*Birth|DOB|Birth\s*Date)[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    ])
    phone = _find([
        r"(?:Home\s*Phone|Cell\s*Phone|Phone\s*No|Telephone)[:\s]+([\(\d][\d\s\(\)\-\.]{7,16}\d)",
    ])
    email = _find([
        r"(?:E-?mail)[:\s]+([\w\.\+\-]+@[\w\.\-]+\.\w{2,})",
        r"\b([\w\.\+\-]+@[\w\.\-]+\.\w{2,})\b",
    ])
    present_address = _find([
        r"(?:Present\s*Address|Current\s*Address|Mailing\s*Address)[:\s]+([0-9][^\n]{4,80})",
        r"(?:Residing\s*at|Lives?\s*at)[:\s]+([0-9][^\n]{4,60})",
    ])
    previous_address = _find([
        r"(?:Former\s*Address|Previous\s*Address|Prior\s*Address)[:\s]+([0-9][^\n]{4,80})",
        r"(?:If\s*residing\s*at|If\s*less\s*than\s*\d)[^\n]{0,20}:\s*([0-9][^\n]{4,60})",
    ])

    # ── Employment ──────────────────────────────────────────────────────────
    employers = re.findall(
        r"(?:Employer'?s?\s*Name|Name\s*of\s*Employer|Employer)[:\s]+([^\n]{3,60})",
        text, re.IGNORECASE,
    )
    employer = employers[0].strip() if employers else ""
    co_employer = employers[1].strip() if len(employers) >= 2 else ""

    employer_phone = _find([
        r"(?:Business\s*Phone|Employer\s*Phone|Work\s*Phone|Office\s*Phone)[:\s]+([\(\d][\d\s\(\)\-\.]{7,16}\d)",
    ])
    position = _find([
        r"(?:Position\/Title|Job\s*Title|Position|Title\s*of\s*Position)[:\s]+([^\n]{2,50})",
        r"(?:Self-?Employed\s*as|Type\s*of\s*Business)[:\s]+([^\n]{2,40})",
    ])
    years_on_job = _find([
        r"(?:Years\s*on\s*(?:this\s*)?[Jj]ob|Time\s*on\s*Job)[:\s]+([^\n]{1,20})",
        r"(\d+\.?\d*)\s+[Yy]ears?\s+(?:on|at|with)\s+",
    ])
    years_in_field = _find([
        r"(?:Years\s*employed\s*in\s*this|Total\s*years\s*in)[:\s]+([^\n]{1,20})",
        r"(\d+\.?\d*)\s+years?\s+(?:in\s+)?(?:this\s+)?(?:field|industry|profession|line)",
    ])
    base_income = _find([
        r"(?:Base\s*(?:Employ\.?\s*)?Income|Monthly\s*Gross\s*Income|Gross\s*Monthly\s*Income)[:\s]+\$?([\d,\.]+)",
    ])

    # ── Loan info ────────────────────────────────────────────────────────────
    loan_amount = _find([
        r"(?:Loan\s*Amount|Amount\s*of\s*(?:this\s*)?(?:Loan|Mortgage)|Mortgage\s*Amount)[:\s]+\$?([\d,\.]+)",
    ])
    property_address = _find([
        r"(?:Subject\s*Property\s*Address|Property\s*Street\s*Address|Property\s*Address)[:\s]+([^\n]{5,100})",
    ])
    loan_purpose = _find([
        r"(?:Purpose\s*of\s*(?:the\s*)?Loan|Loan\s*Purpose)[:\s]+([^\n]{3,40})",
    ])
    property_use = _find([
        r"(?:Property\s*will\s*be\s*used|Occupancy\s*Type|Property\s*Use)[:\s]+([^\n]{3,40})",
    ])
    interest_rate = _find([
        r"(?:Interest\s*Rate|Note\s*Rate)[:\s]+(\d+\.?\d*\s*%)",
    ])
    loan_term = _find([
        r"(?:Number\s*of\s*Months|Loan\s*Term|Term\s*of\s*Loan)[:\s]+(\d+\s*(?:months?|years?)?)",
    ])
    property_value = ""  # populated by smart fallback if available

    # ── Clean up template-text artifacts BEFORE smart fallback ───────────────
    # Reject values that are clearly template text, not real data
    _TEMPLATE_JUNK = [
        'or Business Name', 'or Title', 'Street Unit', 'First, Middle, Last',
        'mm/dd/yyyy', 'specify', 'Purchase Refinance', 'explain',
        'Uniform Residential', 'Freddie Mac', 'Fannie Mae', 'Calyx Form',
        'information as directed', 'Section 1:', 'Section 2:', 'Section 3:',
        'Section 4:', 'INFORMATION', 'This section',
    ]
    def _is_template(val):
        if not val:
            return False
        for t in _TEMPLATE_JUNK:
            if t.lower() in val.lower():
                return True
        return False

    if _is_template(borrower_name):
        borrower_name = ""
    if _is_template(employer):
        employer = ""
    if _is_template(position):
        position = ""
    if _is_template(loan_purpose):
        loan_purpose = ""
    if _is_template(property_address):
        property_address = ""
    if _is_template(present_address):
        present_address = ""
    if _is_template(loan_amount):
        loan_amount = ""
    if _is_template(property_use):
        property_use = ""
    if _is_template(co_employer):
        co_employer = ""

    # ═══════════════════════════════════════════════════════════════════════════
    # SMART FALLBACK — Structural extraction for URLA / Calyx-generated PDFs
    # ═══════════════════════════════════════════════════════════════════════════
    # Calyx-generated 1003 PDFs (and similar) put template text at the top of
    # each page and actual filled values in a data blob at the bottom, after
    # the standard URLA footer ("Calyx Form - ...\nEffective MM/YYYY").
    # We split on those footers to extract the data blobs.

    _urla_blobs = re.split(
        r'Calyx\s+Form[^\n]*\n\.?\s*\n?Effective\s+\d+/\d+',
        text
    )

    # Also handle non-Calyx URLA forms: split on "Freddie Mac Form 65" footer
    if len(_urla_blobs) < 2:
        _urla_blobs = re.split(
            r'Freddie\s+Mac\s+Form\s+65\s+.*?Fannie\s+Mae\s+Form\s+1003\s*\n',
            text, flags=re.DOTALL
        )

    if len(_urla_blobs) > 1:
        # Collect all blob lines from all pages
        _all_1003_blob_lines = []
        _page_blobs = []  # list of (page_idx, [lines])

        for _bi, _blob_text in enumerate(_urla_blobs[1:], 1):
            _blob_text = _blob_text.strip()
            if not _blob_text:
                continue
            # The data blob is everything before the next page's template starts.
            # Template pages start with section headers like "Section X:" or
            # "To be completed by" or long boilerplate.
            # Take lines until we hit a clearly template line (>80 chars of text).
            _blob_lines = []
            for _line in _blob_text.split('\n'):
                _ls = _line.strip()
                if not _ls:
                    continue
                # Stop at next template section (long lines with legal text)
                if len(_ls) > 100 and not re.match(r'^[A-Z][a-z]', _ls):
                    break
                if _ls.startswith('Section ') and ':' in _ls:
                    break
                if _ls.startswith('To be completed by'):
                    break
                if _ls.startswith('Uniform Residential Loan'):
                    break
                # Skip URLA footer remnants
                if 'Freddie Mac Form' in _ls or 'Fannie Mae Form' in _ls:
                    continue
                if _ls.startswith('Calyx Form'):
                    continue
                if re.match(r'^Effective\s+\d+/\d+', _ls):
                    continue
                if _ls == '.' or _ls == '#ADV':
                    continue
                # Skip originator line at end of pages
                if 'NMLSR#' in _ls or 'LIC#' in _ls:
                    continue
                if _ls.startswith('Borrower Name'):
                    continue
                _blob_lines.append(_ls)
                _all_1003_blob_lines.append(_ls)
            _page_blobs.append((_bi, _blob_lines))

        # ── Parse page 1 blob: borrower info + employment ──
        # Page 1 blob structure (Calyx URLA):
        #   [loan_id], name, SSN, DOB, [citizenship], [dependents] phone,
        #   email, address_street, address_city, [years rent], [country],
        #   [former_street], [former_city], [years], income, total_income,
        #   employer [phone], [employer_addr], [employer_city], position,
        #   [start_date], [years months], gross_income
        if _page_blobs:
            _p1_lines = _page_blobs[0][1]

            # Helper: find first line matching a test
            def _blob_find(lines, test_fn, start=0):
                for _idx in range(start, len(lines)):
                    if test_fn(lines[_idx]):
                        return _idx, lines[_idx]
                return -1, ""

            # Borrower name: first line that looks like a person name (2+ cap words)
            if not borrower_name:
                for _ln in _p1_lines:
                    if (re.match(r'^[A-Z][a-z]+\s+[A-Z][a-zA-Z\'\-]+', _ln)
                            and len(_ln) < 60
                            and not re.search(r'\d{3}', _ln)  # no phone/SSN
                            and '@' not in _ln):
                        borrower_name = _ln.strip()
                        break

            # DOB: first standalone date in MM/DD/YYYY format
            if not dob:
                for _ln in _p1_lines:
                    _dm = re.match(r'^(\d{2}/\d{2}/\d{4})$', _ln.strip())
                    if _dm:
                        dob = _dm.group(1)
                        break

            # Phone: find a line containing a 10-digit phone pattern
            if not phone:
                for _ln in _p1_lines:
                    _pm = re.search(r'(\d{3}[\-\.\s]?\d{3}[\-\.\s]?\d{4})', _ln)
                    if _pm:
                        _candidate = _pm.group(1)
                        # Skip SSN-like patterns
                        if not re.match(r'\d{3}-\d{2}-\d{4}', _candidate):
                            phone = _candidate
                            break

            # Present address: first line starting with a street number
            if not present_address:
                for _i, _ln in enumerate(_p1_lines):
                    if re.match(r'^\d{1,6}\s+[A-Z]', _ln):
                        present_address = _ln
                        # Check if next line is City State ZIP
                        if _i + 1 < len(_p1_lines):
                            _next = _p1_lines[_i + 1]
                            if re.match(r'^[A-Z][a-z]+\s+[A-Z]{2}\s+\d{5}', _next):
                                present_address += ", " + _next
                        break

            # Former address: second address-like line
            if not previous_address:
                _found_first = False
                for _i, _ln in enumerate(_p1_lines):
                    if re.match(r'^\d{1,6}\s+[A-Z]', _ln):
                        if _found_first:
                            previous_address = _ln
                            if _i + 1 < len(_p1_lines):
                                _next = _p1_lines[_i + 1]
                                if re.match(r'^[A-Z][a-z]+\s+[A-Z]{2}\s+\d{5}', _next):
                                    previous_address += ", " + _next
                            break
                        _found_first = True

            # Employer: line with company name (often followed by phone digits)
            if not employer:
                for _ln in _p1_lines:
                    # Employer lines often have name + phone concatenated
                    _em = re.match(r'^([A-Z][a-zA-Z\s\.\,\&\'\-]+?)\s+(\d{10})$', _ln)
                    if _em:
                        employer = _em.group(1).strip()
                        if not employer_phone:
                            _raw = _em.group(2)
                            employer_phone = f"{_raw[:3]}-{_raw[3:6]}-{_raw[6:]}"
                        break
                # Fallback: look for lines that appear after income amounts
                if not employer:
                    _after_income = False
                    for _ln in _p1_lines:
                        if re.match(r'^[\d,]+\.\d{2}$', _ln):
                            _after_income = True
                            continue
                        if _after_income and re.match(r'^[A-Z]', _ln) and len(_ln) > 3:
                            if not re.match(r'^\d', _ln) and '@' not in _ln:
                                # Could be employer or employer address
                                if not re.match(r'^(?:PO Box|\d)', _ln):
                                    employer = re.sub(r'\s+\d{10,}$', '', _ln).strip()
                                    break

            # Position: look for job title keywords or short capitalized text after employer
            if not position or position.lower().startswith('or '):
                for _ln in _p1_lines:
                    _ln_l = _ln.lower()
                    if _ln_l in ['consultant', 'manager', 'engineer', 'analyst',
                                  'director', 'nurse', 'teacher', 'accountant',
                                  'attorney', 'agent', 'broker', 'officer',
                                  'technician', 'specialist', 'coordinator',
                                  'supervisor', 'administrator', 'assistant',
                                  'associate', 'developer', 'designer', 'sales',
                                  'executive', 'president', 'vp', 'ceo', 'cfo']:
                        position = _ln
                        break
                # Broader: line after employer city that is a short title-like word
                if not position or position.lower().startswith('or '):
                    _found_employer_city = False
                    for _ln in _p1_lines:
                        if _found_employer_city:
                            # Position is typically a short word/phrase, not a number or date
                            if (len(_ln) < 40 and re.match(r'^[A-Z]', _ln)
                                    and not re.match(r'^\d', _ln)
                                    and '/' not in _ln and '@' not in _ln
                                    and not re.match(r'^(?:PO Box|United)', _ln)):
                                position = _ln
                                break
                        # Employer city line: "City ST ZIPCODE"
                        if re.match(r'^[A-Z][a-z]+\s+[A-Z]{2}\s+\d{5}', _ln):
                            # Could be address city OR employer city — track the second one
                            _found_employer_city = True

            # Base income: look for dollar amounts in the blob
            if not base_income:
                for _ln in _p1_lines:
                    _im = re.match(r'^([\d,]+\.\d{2})$', _ln.strip())
                    if _im:
                        try:
                            _val = float(_im.group(1).replace(',', ''))
                            if 500 <= _val <= 100000:  # reasonable monthly income
                                base_income = _im.group(1)
                                break
                        except ValueError:
                            pass

            # Years on job: find start date (MM/DD/YYYY after position/employer city)
            # and "X Y" pattern = years months in line of work
            _found_position = False
            for _i, _ln in enumerate(_p1_lines):
                if _ln == position:
                    _found_position = True
                    continue
                if _found_position:
                    # Start date: MM/DD/YYYY
                    _sd = re.match(r'^(\d{2}/\d{2}/\d{4})$', _ln)
                    if _sd and not years_on_job:
                        _start_str = _sd.group(1)
                        try:
                            from datetime import datetime as _dt
                            _start = _dt.strptime(_start_str, '%m/%d/%Y')
                            _now = _dt.now()
                            _years = (_now - _start).days / 365.25
                            years_on_job = f"{_years:.1f} years (started {_start_str})"
                        except Exception:
                            years_on_job = f"Started {_start_str}"
                        continue
                    # Years/months pattern: "3 0" or "5 6"
                    _ym = re.match(r'^(\d{1,2})\s+(\d{1,2})$', _ln)
                    if _ym and not years_in_field:
                        _yrs = int(_ym.group(1))
                        _mos = int(_ym.group(2))
                        if _mos > 0:
                            years_in_field = f"{_yrs} years {_mos} months"
                        else:
                            years_in_field = f"{_yrs} years"
                        break  # done with employment section

        # ── Parse page 5 blob (or whichever has loan info) ──
        # Loan amount and property address
        for _pi, _plines in _page_blobs:
            if not _plines:
                continue
            # Loan amount: large dollar value (typically first line of loan section)
            if not loan_amount:
                for _ln in _plines:
                    _lm = re.match(r'^([\d,]+\.\d{2})$', _ln.strip())
                    if _lm:
                        try:
                            _val = float(_lm.group(1).replace(',', ''))
                            if _val >= 50000:
                                loan_amount = _lm.group(1)
                                break
                        except ValueError:
                            pass

            # Property address from blob: "City ST ZIP COUNTY" pattern
            if not property_address or property_address.lower().startswith('street'):
                for _i, _ln in enumerate(_plines):
                    _addr_m = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([A-Z]{2})\s+(\d{5})\s+([A-Z]+)$', _ln)
                    if _addr_m:
                        _city = _addr_m.group(1)
                        _state = _addr_m.group(2)
                        _zip = _addr_m.group(3)
                        _county = _addr_m.group(4)
                        # Check if prev line has street address
                        _street = ""
                        if _i > 0:
                            _prev = _plines[_i-1]
                            if re.match(r'^\d', _prev):
                                _street = _prev
                            elif _prev == 'TBD':
                                _street = "TBD"
                        if _street and _street != 'TBD':
                            property_address = f"{_street}, {_city}, {_state} {_zip}"
                        elif _street == 'TBD':
                            property_address = f"TBD, {_city}, {_state} {_zip} ({_county} County)"
                        else:
                            property_address = f"{_city}, {_state} {_zip}"
                        break

            # Property value: "N VALUE" pattern (units + value on same line)
            for _ln in _plines:
                _pv = re.match(r'^(\d)\s+([\d,]+)$', _ln)
                if _pv:
                    try:
                        _val = float(_pv.group(2).replace(',', ''))
                        if _val >= 50000:
                            property_value = f"${_pv.group(2)} ({_pv.group(1)} unit{'s' if _pv.group(1) != '1' else ''})"
                            break
                    except ValueError:
                        pass

    # Loan purpose: detect from text if template captured all options
    if not loan_purpose:
        if re.search(r'Loan\s*Purpose.*?Purchase', text, re.IGNORECASE):
            # Check for actual purchase indicators
            if re.search(r'(?:Sales\s+Contract\s+Price|Purchase\s+Price)', text, re.IGNORECASE):
                loan_purpose = "Purchase"

    # ── Missing required fields check ────────────────────────────────────────
    required = {
        "Borrower Name": borrower_name,
        "SSN": ssn,
        "Present Address": present_address,
        "Employer": employer,
        "Loan Amount": loan_amount,
        "Property Address": property_address,
    }
    missing = [k for k, v in required.items() if not v]

    return {
        "borrower": {
            "name": borrower_name,
            "ssn": ssn,
            "dob": dob,
            "phone": phone,
            "email": email,
            "present_address": present_address,
            "previous_address": previous_address,
        },
        "co_borrower": {
            "name": co_borrower_name,
            "ssn": co_ssn,
            "employer": co_employer,
        },
        "employment": {
            "employer": employer,
            "employer_phone": employer_phone,
            "position": position,
            "years_on_job": years_on_job,
            "years_in_field": years_in_field,
            "base_monthly_income": base_income,
        },
        "loan": {
            "amount": loan_amount,
            "purpose": loan_purpose,
            "term": loan_term,
            "interest_rate": interest_rate,
            "property_address": property_address,
            "property_value": property_value,
            "property_use": property_use,
        },
        "missing_required": missing,
    }


# ---------------------------------------------------------------------------
# W-2 Parser
# ---------------------------------------------------------------------------

def extract_w2(text: str) -> dict:
    """
    Extract structured fields from a W-2 Wage and Tax Statement.

    Real-world W-2 PDFs (Calyx, ADP, etc.) extract as template label text
    followed by bare data values on their own lines — NOT as "Label: value"
    pairs. This parser handles that positional format.

    Example extracted text pattern:
        b Employer identification number (EIN)
        83-1394635
        c Employer's name, address, and ZIP code
        SECURED MORTGAGE PROCESSING, LLC
        18798 E DRUIDS GLEN RD
        XXX-XX-5779
        1106 NEWCASTLE DR
        1245.00
        1245.00 77.19
        1245.00 18.05
        QUEEN CREEK AZ 85142
        BRICE LEASURE
        OLD HICKORY TN 37138
        Form W-2 Wage and Tax Statement 2025
    """
    import re

    def _money(val):
        if not val:
            return 0.0
        try:
            return float(re.sub(r'[^\d.]', '', str(val)))
        except Exception:
            return 0.0

    # ── Split into one block per W-2 copy ─────────────────────────────────
    # Each copy starts with "Form W-2 Wage and Tax Statement YYYY" or
    # "a Employee's social security number" header.
    # We split on the form year line which appears once per copy.
    raw_blocks = re.split(
        r'(?=(?:a\s+Employee.{0,30}social\s+security|Form\s+W-?2\s+Wage\s+and\s+Tax\s+Statement\s+\d{4}))',
        text, flags=re.IGNORECASE
    )
    raw_blocks = [b.strip() for b in raw_blocks if len(b.strip()) > 80]
    if not raw_blocks:
        raw_blocks = [text]

    def _parse_block(block):
        """Parse one W-2 copy block into a record dict."""

        # ── Tax year ──────────────────────────────────────────────────────
        year = ""
        m = re.search(r'(?:Wage\s+and\s+Tax\s+Statement|Form\s+W-?2)\s+(20\d{2})', block, re.IGNORECASE)
        if m:
            year = m.group(1)
        if not year:
            # Year embedded in OMB line or elsewhere
            m = re.search(r'\b(20\d{2})\b', block)
            if m:
                year = m.group(1)

        # ── SSN (masked or plain) — appears right after "social security number" label ──
        employee_ssn = ""
        m = re.search(r'(?:Employee.{0,30}social\s+security\s+number)\s*\n([^\n]{8,20})', block, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if re.search(r'[\dX\*]{3}[-\s][\dX\*]{2}[-\s][\dX\*\d]{4}', candidate):
                employee_ssn = candidate
        if not employee_ssn:
            m = re.search(r'(XXX-XX-\d{4}|\d{3}-\d{2}-\d{4}|\*{3}-\*{2}-\d{4})', block)
            if m:
                employee_ssn = m.group(1)

        # ── EIN — line after "Employer identification number (EIN)" ──────
        employer_ein = ""
        m = re.search(r'Employer\s+identification\s+number[^\n]*\n([^\n]{5,20})', block, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if re.match(r'[\d\-]{9,12}$', candidate):
                employer_ein = candidate
        if not employer_ein:
            m = re.search(r'\b(\d{2}-\d{7})\b', block)
            if m:
                employer_ein = m.group(1)

        # ── Employer name — first ALL-CAPS or Title-Case line after EIN ──
        employer_name = ""
        m = re.search(
            r'Employer\s+identification\s+number[^\n]*\n[^\n]+\n'   # EIN label + EIN value
            r'[^\n]*Employer.{0,30}name[^\n]*\n([^\n]{3,60})',       # name label + name value
            block, re.IGNORECASE
        )
        if m:
            employer_name = m.group(1).strip()
        if not employer_name:
            # Direct: line after EIN that looks like a company name (letters + spaces)
            m = re.search(r'(\d{2}-\d{7})\s*\n([A-Z][A-Z ,\.\-\'&]+(?:LLC|INC|CORP|CO|LTD|LP)?)', block)
            if m:
                employer_name = m.group(2).strip()

        # ── Employee name — appears after employee address block ──────────
        # In these PDFs the data blob order is:
        #   EIN, employer name, employer addr lines, SSN, employee addr, wages block,
        #   employee city/state/zip, EMPLOYEE NAME, employee city/state/zip
        employee_name = ""
        # Strategy: find all-caps name lines (2+ words, each word 2+ letters)
        name_candidates = re.findall(
            r'^([A-Z][A-Z\-\']{1,}\s+[A-Z][A-Z\-\']{1,}(?:\s+[A-Z][A-Z\-\']{1,})?)$',
            block, re.MULTILINE
        )
        _skip = {
            'SECURED MORTGAGE PROCESSING', 'WAGE AND TAX STATEMENT',
            'DEPARTMENT OF THE TREASURY', 'INTERNAL REVENUE SERVICE',
            'COPY B', 'COPY C', 'NOTICE TO EMPLOYEE', 'VOID', 'CORRECTED',
            'EMPLOYER NAME', 'EMPLOYEE NAME', 'NEW MARKET',
        }
        for nc in name_candidates:
            parts = nc.split()
            # Each part must be at least 2 chars and not all same letter
            if all(len(p) >= 2 for p in parts) and nc.upper() not in _skip and not re.search(r'\d', nc):
                # Skip if looks like an address or state abbreviation phrase
                if not re.search(r'\b(TN|AL|TX|CA|FL|GA|NY|OH|PA|VA|NC|SC|AR|KY|MS|MO|OK|AZ|NV|CO|WA|OR|IL|IN|MI|WI|MN|IA|KS|NE|SD|ND|MT|ID|WY|UT|NM|AK|HI|ME|VT|NH|MA|RI|CT|NJ|DE|MD|DC)\b$', nc):
                    employee_name = nc.strip()
                    break

        # ── Wages data block ──────────────────────────────────────────────────
        box1 = box2 = box3 = box4 = box5 = box6 = ""

        # Strategy 1: box labels like "1 Wages, tips" or "Box 1" followed by amount
        def _box(n, src):
            m = re.search(
                r'(?:^|\n)\s*' + str(n) + r'\s+(?:Wages?|Federal|Social|Medicare|[A-Z][^\n]{0,40})\s*\n\s*([\d,]+\.\d{2})',
                src, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1)
            # Same-line: "1 Wages, tips... 123,456.78"
            m = re.search(
                r'(?:^|\n)\s*' + str(n) + r'[a-z]?\s+[A-Z][^\n]{0,60?}([\d,]+\.\d{2})',
                src, re.IGNORECASE | re.MULTILINE)
            if m:
                return m.group(1)
            return ""

        box1 = _box(1, block)
        box2 = _box(2, block)
        box3 = _box(3, block)
        box4 = _box(4, block)
        box5 = _box(5, block)
        box6 = _box(6, block)

        # Strategy 2: if box labels didn't work, use positional money-line cluster
        if not box1:
            money_lines = re.findall(
                r'^([\d,]+\.\d{2})(?:\s+([\d,]+\.\d{2}))?$',
                block, re.MULTILINE
            )
            wage_cluster = []
            for ml in money_lines:
                v1 = _money(ml[0])
                if v1 < 1:
                    continue
                wage_cluster.append(ml)
                if len(wage_cluster) == 3:
                    break

            if len(wage_cluster) >= 1:
                box1 = wage_cluster[0][0]
                box2 = wage_cluster[0][1] if wage_cluster[0][1] else ""
            if len(wage_cluster) >= 2:
                # Only assign box3/5 if values differ from box1 (avoid duplicate reads)
                if wage_cluster[1][0] != box1:
                    box3 = wage_cluster[1][0]
                box4 = wage_cluster[1][1] if wage_cluster[1][1] else ""
            if len(wage_cluster) >= 3:
                if wage_cluster[2][0] != box1 and wage_cluster[2][0] != box3:
                    box5 = wage_cluster[2][0]
                box6 = wage_cluster[2][1] if wage_cluster[2][1] else ""

        # ── State ─────────────────────────────────────────────────────────
        state = ""
        m = re.search(r'\b([A-Z]{2})\s+\d{5}(?:-\d{4})?\b', block)
        if m:
            # Most likely the state in an address
            state = m.group(1)

        return {
            "year": year,
            "employer_name": employer_name,
            "employer_ein": employer_ein,
            "employee_name": employee_name,
            "employee_ssn": employee_ssn,
            "box1_wages": box1,
            "box2_fed_tax": box2,
            "box3_ss_wages": box3,
            "box4_ss_tax": box4,
            "box5_medicare_wages": box5,
            "box6_medicare_tax": box6,
            "box12": "",
            "box14": "",
            "state": state,
            "state_wages": "",
            "state_tax": "",
        }

    # Parse each block
    all_records = [_parse_block(b) for b in raw_blocks]

    # ── Deduplicate: same year + same box1 wages = same W-2 copy ──────────
    seen = set()
    w2_records = []
    for r in all_records:
        if not r["box1_wages"] and not r["employer_name"] and not r["employee_name"]:
            continue
        key = (r["year"], r["box1_wages"], (r["employer_ein"] or r["employer_name"])[:15])
        if key not in seen:
            seen.add(key)
            w2_records.append(r)

    # ── Income calculation ─────────────────────────────────────────────────
    def _money(val):
        if not val:
            return 0.0
        try:
            return float(re.sub(r'[^\d.]', '', str(val)))
        except Exception:
            return 0.0

    by_year = {}
    for r in w2_records:
        yr = r["year"] or "Unknown"
        wages = _money(r["box1_wages"])
        if wages > 0:
            by_year[yr] = by_year.get(yr, 0.0) + wages

    sorted_years = sorted(by_year.keys(), reverse=True)

    income_calc = {}
    if len(sorted_years) >= 2:
        y1, y2 = sorted_years[0], sorted_years[1]
        w1, w2_val = by_year[y1], by_year[y2]
        avg = (w1 + w2_val) / 2
        income_calc = {
            "year1": y1, "year1_wages": w1,
            "year2": y2, "year2_wages": w2_val,
            "two_year_avg": avg,
            "monthly_avg": avg / 12,
            "method": "2-year average",
        }
    elif len(sorted_years) == 1:
        yr = sorted_years[0]
        wages = by_year[yr]
        income_calc = {
            "year1": yr, "year1_wages": wages,
            "monthly_avg": wages / 12,
            "method": "single year",
        }

    return {
        "w2_records": w2_records,
        "income_calc": income_calc,
        "by_year": by_year,
    }


# Purchase Contract Parser
# ---------------------------------------------------------------------------

def extract_purchase_contract(text: str) -> dict:
    """
    Extract structured fields from a residential purchase contract.
    Returns parties, transaction terms, agents, title, and contingencies.
    100% offline — regex only.

    Handles real-world PDF extraction output from common contract forms:
    MN STAR, WI WB, AZ REALTORS, CA CAR, and standard REALTORS forms.
    Filters out blank lines (underscores), page numbers, and template phrases.
    """
    import re

    # ── Junk filter — applied to every extracted value ────────────────────────
    _JUNK_PHRASES = [
        "will be represented by", "shall be represented by",
        "hereinafter referred to", "hereinafter called",
        "named above", "described herein", "set forth herein",
        "if applicable", "see attached", "as applicable",
        "as specified below", "as specified herein", "as specified",
        "as described below", "as indicated below", "as indicated herein",
        "n/a", "none", "tbd", "to be determined",
        "agent name", "broker name", "company name",
        "the lending", "the lender",
        "tel.:", "phone:", "email:",
        "name)", "(name",
    ]

    # Single-word all-caps role labels that are NOT people's names
    _ROLE_LABELS = {
        "landlord", "tenant", "lessor", "lessee", "seller", "buyer",
        "grantor", "grantee", "trustee", "trustor", "vendor", "vendee",
        "mortgagor", "mortgagee", "owner", "purchaser",
    }

    def _clean(val: str) -> str:
        """Return cleaned value or empty string if it looks like junk."""
        if not val:
            return ""
        val = val.strip()
        # All underscores / dashes / blanks → blank form field
        if re.match(r'^[\s_\-\.]{3,}$', val):
            return ""
        # Mostly underscores (fill-in-the-blank line)
        if len(val) > 4 and val.count('_') / len(val) > 0.25:
            return ""
        # Strip trailing page numbers like "...something 167"
        val = re.sub(r'\s+\d{1,3}\s*$', '', val).strip()
        # Pure number after stripping → page number
        if re.match(r'^\d+$', val.replace(',', '').replace('.', '')):
            return ""
        # Too short to be meaningful
        if len(val) < 3:
            return ""
        # Reject placeholder patterns like "- Agent Name" or "- Office Name"
        if re.match(r'^-\s+[A-Z][a-z]+\s+[A-Z][a-z]+', val):
            return ""
        # Reject "- Name" single-word placeholder
        if re.match(r'^-\s*[A-Z][a-z]+$', val):
            return ""
        # Template junk phrases
        val_lower = val.lower()
        for phrase in _JUNK_PHRASES:
            if val_lower.startswith(phrase) or val_lower == phrase:
                return ""
        # All-caps multi-word form title (e.g. "REAL ESTATE PURCHASE CONTRACT")
        if val.isupper() and len(val) > 8 and ' ' in val and not re.search(r'\d', val):
            return ""
        # Contains signature/initials — signature line, not a name
        if re.search(r'\b(?:signature|initials?)\b', val_lower):
            return ""
        return val

    def _truncate_at_separator(val: str) -> str:
        """Truncate value at middle-dot (·) or pipe (|) separators used by some PDFs."""
        # Middle dot (U+00B7) and bullet (•) are used as field separators in some PDFs
        val = re.split(r'\s*[·•|]\s*', val)[0].strip()
        return val

    def _find(patterns, default=""):
        """Search patterns, return first non-junk match."""
        for p in patterns:
            try:
                m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
                if m:
                    val = (m.group(1) if m.lastindex else m.group(0)).strip()
                    val = _truncate_at_separator(val)
                    val = re.sub(r'\s+', ' ', val)
                    val = _clean(val)
                    if val:
                        return val
            except re.error:
                continue
        return default

    def _find_name(patterns):
        """
        Like _find but additionally requires the result to look like a person or
        company name — not a pronoun, template phrase, or form boilerplate.
        """
        _NAME_JUNK = [
            "will ", "shall ", "herein", "agent", "broker", "licensee",
            "represent", "the buyer", "the seller", "purchaser herein",
            "and seller", "and buyer", "named below", "whose address",
            "as specified", "as described", "as indicated",
            "see attached", "see exhibit",
            "- agent name", "agent name", "buyers agent", "sellers agent",
            "- office name", "office name", "brokerage name",
            "- contact name", "contact name",
            "financing-buyer", "financing buyer", "buyer financing",
        ]
        for p in patterns:
            try:
                m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
                if m:
                    val = (m.group(1) if m.lastindex else m.group(0)).strip()
                    val = _truncate_at_separator(val)
                    val = re.sub(r'\s+', ' ', val)
                    val = _clean(val)
                    if not val:
                        continue
                    # Must contain at least one letter sequence ≥ 2 chars
                    if not re.search(r'[A-Za-z]{2,}', val):
                        continue
                    # Reject template placeholders that are fully parenthesized: "(Agent Name)"
                    if val.startswith('(') and val.endswith(')'):
                        continue
                    # Reject bare "Name)" type fragments (no opening paren)
                    if val.endswith(')') and '(' not in val:
                        continue
                    # Reject if it contains a dollar sign (commission/price text)
                    if '$' in val:
                        continue
                    # Strip at section-keyword boundaries (prevents cross-line pollution)
                    for _bnd in ['seller', 'buyer', 'property', 'purchase', 'price',
                                 'closing', 'earnest', 'title', 'listing', 'selling',
                                 'escrow', 'addendum', 'contingenc']:
                        _bm = re.search(r'\b' + _bnd + r'\b', val, re.IGNORECASE)
                        if _bm and _bm.start() > 3:
                            val = val[:_bm.start()].strip()
                    # Strip trailing articles/prepositions (cross-line leftovers)
                    val = re.sub(r'\s+(?:The|A|An|At|In|On|Of|For|By|To|Is)\s*$', '', val, flags=re.IGNORECASE).strip()
                    val = _clean(val)
                    if not val:
                        continue
                    val_lower = val.lower()
                    # Reject if it starts with a junk phrase
                    if any(val_lower.startswith(j) or val_lower == j.strip()
                           for j in _NAME_JUNK):
                        continue
                    # Reject single all-caps words that are role labels, not names
                    if val.upper() == val and ' ' not in val.strip():
                        if val_lower in _ROLE_LABELS:
                            continue
                    # Reject if it's all caps and long (likely a section header)
                    if val.isupper() and len(val) > 20:
                        continue
                    return val
            except re.error:
                continue
        return ""

    def _find_address(patterns):
        """Like _find but result must contain a digit (real address)."""
        for p in patterns:
            try:
                m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
                if m:
                    val = (m.group(1) if m.lastindex else m.group(0)).strip()
                    val = re.sub(r'\s+', ' ', val)
                    val = _clean(val)
                    if val and re.search(r'\d', val):
                        return val
            except re.error:
                continue
        return ""

    def _find_price(patterns, min_val=10000):
        """Like _find but result must be a dollar amount ≥ min_val."""
        for p in patterns:
            try:
                m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
                if m:
                    val = (m.group(1) if m.lastindex else m.group(0)).strip()
                    val = re.sub(r'[^\d,.]', '', val)
                    try:
                        num = float(val.replace(',', ''))
                        if num >= min_val:
                            return f"{num:,.0f}" if num == int(num) else f"{num:,.2f}"
                    except ValueError:
                        continue
            except re.error:
                continue
        return ""

    def _find_company(patterns):
        """Like _find but rejects values with dollar signs or that are too short."""
        for p in patterns:
            try:
                m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
                if m:
                    val = (m.group(1) if m.lastindex else m.group(0)).strip()
                    val = _truncate_at_separator(val)
                    val = re.sub(r'\s+', ' ', val)
                    val = _clean(val)
                    if not val:
                        continue
                    # Reject if it contains a dollar sign (commission/price text)
                    if '$' in val:
                        continue
                    # Reject template placeholders ending with )
                    if val.endswith(')'):
                        continue
                    # Reject values starting with a digit (section numbers like "7. TITLE:")
                    if re.match(r'^\d', val):
                        continue
                    # Company names should be at least 4 chars
                    if len(val) < 4:
                        continue
                    # Strip trailing verbs/phrases like "shall handle closing"
                    val = re.sub(r'\s+(?:shall|will|to|is|has|for)\s+.*$', '', val, flags=re.IGNORECASE).strip()
                    # Reject values that start with a verb (residual after label match)
                    if re.match(r'^(?:shall|will|to|is|has|for|handle|at|the)\b', val, re.IGNORECASE):
                        continue
                    # Reject section headers like "Selling Brokerage:" or "Listing Brokerage:"
                    if re.match(r'^(?:selling|listing|buyer|seller)\s*(?:brokerage|office|agent|name)?:', val, flags=re.IGNORECASE):
                        continue
                    if len(val) < 4:
                        continue
                    return val
            except re.error:
                continue
        return ""

    # ── Parties ──────────────────────────────────────────────────────────────
    buyer_name = _find_name([
        # Standard labels
        r"BUYER[S]?\s*[:\(]\s*([A-Z][a-zA-Z'\-]+(?:\s+(?:and\s+)?[A-Z][a-zA-Z'\-]+){1,5})",
        r"^BUYER[S]?\s*[:\|]\s*(.{4,60})$",
        r"Purchaser[s]?\s*:\s*([A-Z][a-zA-Z'\-]+(?:\s+[A-Z][a-zA-Z'\-]+){1,4})",
        r"\d\.\s*BUYER[S]?\s*[:\|]\s*([^\n,]{4,60})",
        r"Buyer\(s\)\s*:\s*([A-Z][a-zA-Z'\-]+(?:\s+(?:and\s+)?[A-Z][a-zA-Z'\-]+){1,5})",
        # Quoted names
        r'(?:OFFER\s+FROM|offer\s+from)\s+([A-Z][a-zA-Z\'\-]+(?:\s+(?:and\s+)?[A-Z][a-zA-Z\'\-]+){1,5})\s*\(',
        r'([A-Z][a-zA-Z\'\-]+(?:\s+(?:and\s+)?[A-Z][a-zA-Z\'\-]+){1,5})\s*\(\s*["\u201c]Buyer',
        r'["\u201c\u201d]Buyer["\u201c\u201d][,\s]+([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+){1,4})',
        r'Buyer\s*[:\|/]\s*[_\s]*([A-Z][a-zA-Z\s\'\-]{3,40}?)(?:\s+Date|$)',
        # All variations: Buyer, Purchaser, Property Owner, Owner
        r'(?i)buyer\s*:\s*([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+){1,4})',
        r'(?i)^buyer\s*:\s*\n\s*([A-Z][^\n]{3,50})',
        r"(?i)BUYER:\s*([A-Z][a-zA-Z'\.][^\n]{3,50})",
        r"(?i)Purchaser['\s]?:\s*([A-Z][^\n]{3,50})",
        r"(?i)Purchaser:\s*([A-Z][^\n]{3,50})",
        r"(?i)Buyer:\s*([A-Z][^\n]{3,50})",
        r"(?i)Property\s+Owner:\s*([A-Z][^\n]{3,50})",
        r"(?i)Owner:\s*([A-Z][^\n]{3,50})",
        # Vermont dotloop signatures
        r"(?m)^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)\.?\s*$)",
    ])

    seller_name = _find_name([
        # Standard labels
        r"SELLER[S]?\s*[:\(]\s*([A-Z][a-zA-Z'\-]+(?:\s+(?:and\s+)?[A-Z][a-zA-Z'\-]+){1,5})",
        r"^SELLER[S]?\s*[:\|]\s*(.{4,60})$",
        r"\d\.\s*SELLER[S]?\s*[:\|]\s*([^\n,]{4,60})",
        r"Seller\(s\)\s*:\s*([A-Z][a-zA-Z'\-]+(?:\s+(?:and\s+)?[A-Z][a-zA-Z'\-]+){1,5})",
        r'([A-Z][a-zA-Z\'\-]+(?:\s+(?:and\s+)?[A-Z][a-zA-Z\'\-]+){1,5})\s*\(\s*["\u201c]Seller',
        r'["\u201c\u201d]Seller["\u201c\u201d][,\s]+([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+){1,4})',
        r'Seller\s*[:\|/]\s*[_\s]*([A-Z][a-zA-Z\s\'\-]{3,40}?)(?:\s+Date|$)',
        # All variations: Seller, Vendor, Property Owner
        r'(?i)seller\s*:\s*([A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+){1,4})',
        r'(?i)^seller\s*:\s*\n\s*([A-Z][^\n]{3,50})',
        r"(?i)SELLER:\s*([A-Z][a-zA-Z][^\n]{3,50})",
        r"(?i)Seller:\s*([A-Z][^\n]{3,50})",
        r"(?i)Vendor:\s*([A-Z][^\n]{3,50})",
        r"(?i)Property\s+Owner:\s*([A-Z][^\n]{3,50})",
    ])

    buyer_phone = _find([
        r"(?:Buyer'?s?\s*(?:Phone|Tel|Telephone))[:\s]+([\(\d][\d\s\(\)\-\.]{7,16}\d)",
        r"(?:Buyer'?s?\s*Cell|Buyer\s*Mobile)[:\s]+([\(\d][\d\s\(\)\-\.]{7,16}\d)",
    ])
    buyer_email = _find([
        r"(?:Buyer'?s?\s*E-?mail|Buyer\s*Email)[:\s]+([\w\.\+\-]+@[\w\.\-]+\.\w{2,})",
    ])
    seller_phone = _find([
        r"(?:Seller'?s?\s*(?:Phone|Tel|Telephone))[:\s]+([\(\d][\d\s\(\)\-\.]{7,16}\d)",
    ])
    seller_email = _find([
        r"(?:Seller'?s?\s*E-?mail|Seller\s*Email)[:\s]+([\w\.\+\-]+@[\w\.\-]+\.\w{2,})",
    ])

    # ── Property ─────────────────────────────────────────────────────────────
    property_address = _find_address([
        # Standard labels
        r"(?:Property\s*Address|Subject\s*Property\s*Address)[:\s]+(\d[^\n]{5,100})",
        r"(?:real\s*property\s*(?:known\s*as|located\s*at|described\s*as|situate[d]?\s*at))[:\s,]+(\d[^\n]{5,100})",
        r"(?:located\s+at|property\s+at)[:\s]+(\d[^\n]{5,80})",
        r"(?:Common\s*[Aa]ddress|Street\s*[Aa]ddress)[:\s]+(\d[^\n]{5,80})",
        r"(?:Address\s+of\s+Real\s+Estate|Property\s+Location)[:\s]+(\d[^\n]{5,80})",
        # All variations: Property Address, Subject Property, Property Location, Real Property
        r"(?i)Property\s+Address[:\s]+([^\n]{5,100})",
        r"(?i)Subject\s+Property[:\s]+([^\n]{5,100})",
        r"(?i)Property\s+Location[:\s]+([^\n]{5,100})",
        r"(?i)Real\s+Property[:\s]+([^\n]{5,100})",
        # Standalone address pattern
        r"\b(\d{1,6}\s+[A-Z][a-zA-Z\s]{3,40},\s+[A-Za-z\s]{2,20},\s+[A-Z]{2}\s+\d{5})",
        r"\b(\d{1,6}\s+[A-Z][a-zA-Z\s\.]{3,40}(?:St|Ave|Blvd|Dr|Rd|Ln|Ct|Way|Pl|Circle|Cir)\b[^\n]{0,40})",
    ])

    # ── Transaction ──────────────────────────────────────────────────────────
    purchase_price = _find_price([
        r"(?:Purchase\s*Price|Sales?\s*Price|Contract\s*Price|Offer\s*Price|Total\s*Purchase\s*Price)[:\s]+\$?\s*([\d,]+(?:\.\d{1,2})?)",
        r"\$\s*([\d,]+(?:\.\d{2})?)\s*\([A-Za-z\s]+[Dd]ollars",
        r"sum\s+of\s+\$\s*([\d,]+)",
        r"price\s+(?:of|is)\s+\$\s*([\d,]+)",
        r"agrees?\s+to\s+(?:buy|purchase).*?for.*?\$\s*([\d,]+)",
        r"\$\s*([\d]{2,3},\d{3}(?:\.\d{2})?)\b",
        r"(?m)^([\d]{2,3},\d{3}(?:\.\d{2})?)\s*$",
        # All case variations - Money
        r"(?i)PURCHASE\s+PRICE[:\s]+\$?([\d,]+)",
        r"(?i)SALES\s+PRICE[:\s]+\$?([\d,]+)",
        r"(?i)TOTAL\s+CONSIDERATION[:\s]+\$?([\d,]+)",
        r"(?i)Contract\s+Price[:\s]+\$?([\d,]+)",
        r"(?i)Purchase\s+Amount[:\s]+\$?([\d,]+)",
        r"(?i)Total\s+Purchase\s+Price[:\s]+\$?([\d,]+)",
        r"(?i)Agreed\s+Purchase\s+Price[:\s]+\$?([\d,]+)",
        # Vermont dotloop
        r"\$([\d]{3,6},\d{3})",
    ], min_val=50000)  # purchase price must be ≥ $50,000 to avoid earnest money confusion

    closing_date = _find([
        # Labeled date with specific format (allows commas in "April 30, 2025")
        r"(?:Closing\s*Date|Close\s*of\s*Escrow\s*Date|Settlement\s*Date)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?:Closing\s*Date|Close\s*of\s*Escrow\s*Date|Settlement\s*Date)[:\s]+([^\n]{3,40})",
        # "shall close on/by [date]"
        r"(?:shall\s+close|closing\s+shall\s+(?:occur|take\s+place))\s+(?:on\s+or\s+before\s+|by\s+|on\s+)([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        # "on or before April 15, 2026"
        r"on\s+or\s+before\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{4})",
        # "close by March 28, 2026"
        r"close\s+by\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{4})",
        # "closing date of [date]"
        r"closing\s+date\s+of\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{4})",
        r"(?:close|closing|settlement)\s+(?:on|by|no\s+later\s+than)\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{4})",
        # CA CAR: "Close of Escrow shall be on June 15, 2025"
        r"(?:close\s+of\s+escrow|escrow)\s+shall\s+(?:be\s+)?(?:on|by)\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{4})",
        # Dotloop Ohio: two identical dates on same line = escrow date + title transfer date
        r"(\d{1,2}/\d{1,2}/\d{4})\s+\d{1,2}/\d{1,2}/\d{4}",
        # All case-insensitive variations - Closing Date
        r"(?i)CLOSING\s+DATE[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
        r"(?i)CLOSE\s+ON[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
        r"(?i)CLOSING\s+ON[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
        r"(?i)SETTLEMENT\s+DATE[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
        r"(?i)Estimated\s+Closing[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
        r"(?i)Date\s+of\s+Closing[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
        # Vermont dotloop: directly find MM/DD/YYYY or YYYY-MM-DD dates
        r"(\d{1,2}/\d{1,2}/20\d{2})",
        r"(20\d{2}-\d{2}-\d{2})",
        # Contract Date variations
        r"(?i)Contract\s+Date[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?i)Date\s+of\s+Contract[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?i)Execution\s+Date[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?i)Signed\s+Date[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?i)Effective\s+Date[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?i)Agreement\s+Date[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    ])

    earnest_money = _find_price([
        # Standard labels
        r"(?:Earnest\s*Money\s*(?:Deposit)?|EMD|Initial\s*(?:Earnest\s*Money\s*)?Deposit|Good\s*Faith\s*Deposit)[:\s]+\$?\s*([\d,]+(?:\.\d{1,2})?)",
        r"earnest\s+money\s+of\s+\$?\s*([\d,]+)",
        r"deposit\s+of\s+\$?\s*([\d,]+)\s+(?:as\s+earnest|with\s+offer)",
        r"deposit\s+\$?\s*([\d,]+)\s+as\s+earnest",
        r"(?m)^(\d{1,3},\d{3}\.\d{2})\s*$",
        # All variations: Earnest Money, Earnest Deposit, Initial Deposit, Good Faith Deposit, Deposit, EMD
        r"(?i)Earnest\s+Money[:\s]+\$?([\d,]+)",
        r"(?i)Earnest\s+Deposit[:\s]+\$?([\d,]+)",
        r"(?i)Initial\s+Deposit[:\s]+\$?([\d,]+)",
        r"(?i)Good\s+Faith\s+Deposit[:\s]+\$?([\d,]+)",
        r"(?i)Deposit[:\s]+\$?([\d,]+)",
        r"(?i)EMD[:\s]+\$?([\d,]+)",
    ], min_val=100)

    down_payment = _find_price([
        r"(?:Down\s*Payment|Cash\s*Down\s*Payment|Buyer'?s?\s*Down)[:\s]+\$?\s*([\d,]+(?:\.\d{1,2})?)",
        r"down\s+payment\s+of\s+\$?\s*([\d,]+)",
        # All variations
        r"(?i)Down\s+Payment[:\s]+\$?([\d,]+)",
        r"(?i)Downpayment[:\s]+\$?([\d,]+)",
    ])

    seller_concessions = _find([
        r"(?:Seller\s*(?:Concession|Credit|Contribution)[s]?|Seller\s*(?:to\s*)?(?:Pay|Contribute)[s]?\s*Closing)[:\s]+\$?\s*([\d,]+[^\n]{0,60})",
        r"(?:closing\s+cost\s+(?:credit|contribution)|seller\s+to\s+pay\s+(?:up\s+to\s+)?\$?\s*[\d,]+)[^\n]{0,50}",
        r"Seller\s+(?:agrees\s+to\s+)?(?:pay|contribute|credit)\s+(?:up\s+to\s+)?\$\s*([\d,]+[^\n]{0,40})",
        # All variations
        r"(?i)SELLER\s+CONCESSIONS[:\s]+\$?([\d,]+)",
        r"(?i)SELLER\s+CREDIT[:\s]+\$?([\d,]+)",
        r"(?i)SELLER\s+CONTRIBUTION[:\s]+\$?([\d,]+)",
        r"(?i)Seller\s+Paid\s+Costs[:\s]+\$?([\d,]+)",
        r"(?i)Seller\s+Assistance[:\s]+\$?([\d,]+)",
    ])

    # ── Hard-stop helpers (used by Title, Listing/Selling Agent, Brokerage) ───
    # Names are 2-5 capitalized words; companies are mixed-case with limited punctuation.
    # Both stop at separators (·•|), next-field markers, phone, email, or end-of-line.
    _NAME_BODY = r"[A-Z][a-zA-Z'\-]+(?:\s+(?:and\s+)?[A-Z][a-zA-Z'\-\.]+){0,4}"
    _NAME_STOP = r"(?=\s*(?:[·•|]|Tel|Phone|Email|Fax|Selling|Listing|Title|Brokerage|Broker|License|Agent|Office|Company|of\s|\d{3}[\-\.\s]\d{3}|[\w\.\+\-]+@|$|\n))"
    _CO_BODY   = r"[A-Z][A-Za-z0-9'&,\-\. ]{3,58}?"
    _CO_STOP   = r"(?=\s*(?:[·•|]|Tel|Phone|Email|Fax|Selling|Listing|Title|License|Agent|of\s|\d{3}[\-\.\s]\d{3}|[\w\.\+\-]+@|$|\n))"

    # ── Title company ─────────────────────────────────────────────────────────
    title_company = _find_company([
        r"(?:Title\s*Company|Title\s*Co\.?|Escrow\s*Company|Settlement\s*Agent|Title\s*Insurance\s*(?:Company|Co))[:\s]+(" + _CO_BODY + r")" + _CO_STOP,
        r"(?:closing\s+(?:at|with|through)|escrow\s+(?:at|with|through))\s+(" + _CO_BODY + r")" + _CO_STOP,
        r"([A-Z][a-zA-Z\s]{1,40}(?:Title|Escrow|Settlement)\s+(?:Company|Co\.?|Corp\.?|Inc\.?|LLC|Services?|Group))",
        r"(?m)^([A-Z][^\n\d·•|]{2,60}(?:Title|Escrow|Settlement)[^\n·•|]{0,30})\s*$",
        r"(?i)Title\s+&\s+Escrow[:\s]+(" + _CO_BODY + r")" + _CO_STOP,
        r"(?i)Settlement\s+Company[:\s]+(" + _CO_BODY + r")" + _CO_STOP,
    ])
    title_contact = _find([
        r"(?:Title\s*(?:Officer|Agent|Contact|Rep)|Escrow\s*Officer)[:\s]+([A-Z][^\n_]{3,40})",
    ])
    title_phone = _find([
        r"(?:Title|Escrow)\s*(?:Company)?\s*(?:Phone|Tel)[:\s]+([\(\d][\d\s\(\)\-\.]{7,16}\d)",
    ])
    title_email = _find([
        r"(?:Title|Escrow)\s*(?:Company)?\s*(?:E-?mail|Email)[:\s]+([\w\.\+\-]+@[\w\.\-]+\.\w{2,})",
    ])

# ── Listing / Seller's agent ──────────────────────────────────────────────
    listing_agent = _find_name([
        # "Agent Name of Brokerage" — capture just the name before "of"
        r"(?:Listing\s*Agent|Seller'?s?\s*Agent|Seller'?s?\s*Broker\s*Agent)\s*(?:Name\s*)?[:\s]+(" + _NAME_BODY + r")\s+of\s+",
        # General — hard stop at separators / next field
        r"(?:Listing\s*Agent|Seller'?s?\s*Agent|Seller'?s?\s*Broker\s*Agent)\s*(?:Name\s*)?[:\s]+(" + _NAME_BODY + r")" + _NAME_STOP,
        r"(?:L\.?A\.?\s*Name|Listing\s*Broker\s*Name)[:\s]+(" + _NAME_BODY + r")" + _NAME_STOP,
        r"(?:Seller'?s?\s*Licensee)\s*[:\s]+(" + _NAME_BODY + r")" + _NAME_STOP,
        r"(?i)Listing\s+Broker[:\s]+(" + _NAME_BODY + r")" + _NAME_STOP,
        r"(?i)Seller['\s]?\s+Representative[:\s]+(" + _NAME_BODY + r")" + _NAME_STOP,
        r"(?i)Listing\s+Representative[:\s]+(" + _NAME_BODY + r")" + _NAME_STOP,
    ])

    listing_brokerage = _find_company([
        r"(?:Listing\s*(?:Broker|Brokerage|Office|Company)|Seller'?s?\s*(?:Broker|Brokerage))\s*(?:Name\s*)?[:\s]+(" + _CO_BODY + r")" + _CO_STOP,
        # "Agent: Name of [Brokerage]"
        r"(?:Listing\s*Agent|Seller'?s?\s*Agent)\s*[:\s]+" + _NAME_BODY + r"\s+of\s+(" + _CO_BODY + r")" + _CO_STOP,
    ])
    listing_phone = _find([
        r"(?:Listing\s*Agent\s*(?:Phone|Tel)|L\.?A\.?\s*(?:Phone|Tel))[:\s]+([\(\d][\d\s\(\)\-\.]{7,16}\d)",
    ])
    listing_email = _find([
        r"(?:Listing\s*Agent\s*E-?mail)[:\s]+([\w\.\+\-]+@[\w\.\-]+\.\w{2,})",
    ])

    # ── Selling / Buyer's agent ───────────────────────────────────────────────
    selling_agent = _find_name([
        r"(?:Selling\s*Agent|Buyer'?s?\s*Agent|Cooperating\s*Agent|Co-?op\s*Agent)\s*(?:Name\s*)?[:\s]+(" + _NAME_BODY + r")\s+of\s+",
        r"(?:Selling\s*Agent|Buyer'?s?\s*Agent|Cooperating\s*Agent|Co-?op\s*Agent)\s*(?:Name\s*)?[:\s]+(" + _NAME_BODY + r")" + _NAME_STOP,
        r"(?:S\.?A\.?\s*Name|Selling\s*Broker\s*Name)[:\s]+(" + _NAME_BODY + r")" + _NAME_STOP,
        r"(?:Buyer'?s?\s*Licensee|Buyer'?s?\s*Broker\s*Agent)\s*[:\s]+(" + _NAME_BODY + r")" + _NAME_STOP,
        r"(?:Buyer\s+will\s+be\s+represented\s+by|Buyer'?s?\s+Broker\s+is)\s+(" + _NAME_BODY + r")(?:,|\.|of\s|\(|$)",
        r"(?i)Selling\s+Broker[:\s]+(" + _NAME_BODY + r")" + _NAME_STOP,
        r"(?i)Buyer['\s]?\s+Representative[:\s]+(" + _NAME_BODY + r")" + _NAME_STOP,
    ])
    selling_brokerage = _find_company([
        r"(?:Selling\s*(?:Broker|Brokerage|Office|Company)|Buyer'?s?\s*(?:Broker|Brokerage))\s*(?:Name\s*)?[:\s]+(" + _CO_BODY + r")" + _CO_STOP,
        r"(?:Buyer'?s?\s*Brokerage\s*Name|Buyer'?s?\s*Firm)[:\s]+(" + _CO_BODY + r")" + _CO_STOP,
        r"(?:Selling\s*Agent|Buyer'?s?\s*Agent)\s*[:\s]+" + _NAME_BODY + r"\s+of\s+(" + _CO_BODY + r")" + _CO_STOP,
    ])
    selling_phone = _find([
        r"(?:Selling\s*Agent\s*(?:Phone|Tel)|Buyer'?s?\s*Agent\s*(?:Phone|Tel)|S\.?A\.?\s*(?:Phone|Tel))[:\s]+([\(\d][\d\s\(\)\-\.]{7,16}\d)",
    ])
    selling_email = _find([
        r"(?:Selling\s*Agent\s*E-?mail|Buyer'?s?\s*Agent\s*E-?mail)[:\s]+([\w\.\+\-]+@[\w\.\-]+\.\w{2,})",
    ])

    # ── Dotloop seller — appears immediately after buyer on address/name block ──
    # Structure on page 1 of Ohio dotloop: address → buyer name → seller name
    if not seller_name:
        _seller_m = re.search(
            r'(?m)^\d{1,5}\s+[A-Z][^\n]+,\s+[A-Z]{2}\s+\d{5}\s*\n'
            r'([A-Z][a-z]+(?:\s+[A-Z][a-zA-Z\'\-]+)+)\s*\n'
            r'([A-Z][a-z]+(?:\s+[A-Z][a-zA-Z\'\-]+)+)\s*\n',
            text
        )
        if _seller_m:
            _s_candidate = _seller_m.group(2).strip()
            # Sanity: shouldn't be the same as buyer, shouldn't be an agent brokerage line
            if (_s_candidate != buyer_name
                    and '$' not in _s_candidate
                    and len(_s_candidate) < 60
                    and not _s_candidate.startswith('(')):
                seller_name = _s_candidate

    # ── Keyword-value extraction (works for any contract format) ─────────────
    # Strategy: scan EVERY line for known keywords, then pull the value that
    # immediately follows on the same line or the next non-blank line.
    # Also handles dotloop MLS blocks where labels appear in parentheses.

    # Known form title/header strings that appear in the data block but are not values
    _FORM_TITLES = {
        'real estate purchase contract',
        'purchase agreement',
        'residential purchase contract',
        'multiple listing service information',
        'earnest money deposit receipt',
        'insert initials here',
        'seller signature',
        'buyer signature',
        'seller initials',
        'buyer initials',
        'ohio realtors',
        'realtors',
        'mls information',
        'agency disclosure',
        'addendum',
        'counter offer',
        'lead-based paint',
        'home inspection',
    }

    def _is_template_line(s: str) -> bool:
        """Return True if a line is clearly form template text, not a filled value."""
        s = s.strip()
        if not s:
            return True
        # All underscores or dashes (blank form field)
        if re.match(r'^[\s_\-\.]{3,}$', s):
            return True
        # Mostly underscores
        if len(s) > 4 and s.count('_') / len(s) > 0.25:
            return True
        # Ends with a line number (form template line)
        if re.search(r'\s+\d{1,3}\s*$', s) and len(s) > 20:
            return True
        # dotloop metadata
        if re.match(r'^dotloop', s, re.IGNORECASE):
            return True
        if re.match(r'^dtlp\.us/', s):
            return True
        # Timestamp like "02/14/22 9:53 AM EST"
        if re.match(r'^\d{1,2}/\d{1,2}/\d{2}\s+\d{1,2}:\d{2}', s):
            return True
        # Pure template placeholder in parens
        if s.startswith('(') and s.endswith(')'):
            return True
        # Known form title strings
        if s.lower() in _FORM_TITLES:
            return True
        # All-caps short heading with no digits (form section header like "MLS INFORMATION")
        if s.isupper() and len(s) > 5 and not re.search(r'\d', s) and ' ' in s:
            return True
        return False

    def _kv_next(keyword_pattern: str) -> str:
        """
        Find keyword in text and return the value on the same line after it,
        or on the very next non-blank non-template line.
        Strips dotloop metadata, license numbers, and boilerplate.
        """
        m = re.search(keyword_pattern, text, re.IGNORECASE)
        if not m:
            return ""
        rest = text[m.end():]
        same_line = rest.split('\n')[0].strip()
        same_line = re.sub(r'^[\s:·\-]+', '', same_line).strip()

        if same_line and not _is_template_line(same_line) and len(same_line) >= 2:
            val = same_line
        else:
            # Take first non-template line after keyword
            val = ""
            for _ln in rest.split('\n')[1:]:
                _ln = _ln.strip()
                if not _ln or _is_template_line(_ln):
                    continue
                val = _ln
                break
        if not val:
            return ""
        # Truncate at middle-dot / bullet separators
        val = _truncate_at_separator(val)
        # Remove dotloop verification suffix
        val = re.split(r'dotloop\s+(?:signature|verified)', val, flags=re.IGNORECASE)[0].strip()
        # Remove trailing license numbers (4+ digits, optional "and NNN")
        val = re.sub(r'\s+\d{4,}\s*(?:and\s+\d+)?\s*$', '', val).strip()
        if val.startswith('(') and val.endswith(')'):
            return ""
        return val

    def _kv_phone(line: str) -> str:
        m = re.search(r'(\d{3}[\-\.\s]\d{3}[\-\.\s]\d{4})', line)
        return m.group(1) if m else ""

    def _kv_email(line: str) -> str:
        m = re.search(r'([\w\.\+\-]+@[\w\.\-]+\.\w{2,})', line)
        return m.group(1) if m else ""

    def _kv_name_only(raw: str) -> str:
        """Strip phone/email/license from a raw value, return just the name part."""
        if not raw:
            return ""
        s = re.split(r'\s+\d{3}[\-\.\s]\d{3}[\-\.\s]\d{4}', raw)[0]  # stop before phone
        s = re.split(r'\s+[\w\.\+\-]+@\S+', s)[0]                      # stop before email
        s = re.sub(r'\s+\d{4,}\s*(?:and\s+\d+)?\s*$', '', s).strip()  # strip license
        return s.strip()

    # ── Keyword → field mapping ───────────────────────────────────────────────
    # Each keyword pattern finds a label in the contract text; the value
    # immediately after it (same line or next line) is the real data.

    _LISTING_AGENT_KEYWORDS = [
        r'\(Listing\s+Agent\s+Name\)',
        r'Listing\s+Agent\s*(?:Name)?\s*:',
        r'Seller[\'s]?\s*Agent\s*(?:Name)?\s*:',
        r'L\.?A\.?\s*Name\s*:',
    ]
    _LISTING_BROKERAGE_KEYWORDS = [
        r'\(Listing\s+Brokerage\s+Name\)',
        r'Listing\s+Brokerage\s*(?:Name)?\s*:',
        r'Listing\s+Office\s*(?:Name)?\s*:',
        r'Seller[\'s]?\s*(?:Broker(?:age)?|Brokerage)\s*(?:Name)?\s*:',
    ]
    _SELLING_AGENT_KEYWORDS = [
        r'\(Selling\s+Agent\s+Name\)',
        r'Selling\s+Agent\s*(?:Name)?\s*:',
        r'Buyer[\'s]?\s*Agent\s*(?:Name)?\s*:',
        r'Cooperating\s+Agent\s*(?:Name)?\s*:',
        r'S\.?A\.?\s*Name\s*:',
    ]
    _SELLING_BROKERAGE_KEYWORDS = [
        r'\(Selling\s+Brokerage\s+Name\)',
        r'Selling\s+Brokerage\s*(?:Name)?\s*:',
        r'Selling\s+Office\s*(?:Name)?\s*:',
        r'Buyer[\'s]?\s*(?:Broker(?:age)?|Brokerage)\s*(?:Name)?\s*:',
    ]
    _TITLE_KEYWORDS = [
        r'(?:Title\s+Company|Escrow\s+(?:Company|Agent)|Settlement\s+Agent)\s*:',
        r'(?:closing|escrow)\s+(?:at|with|through)\s+([A-Z])',
        r'Escrow\s+Agent[^.]{0,5}:\s',
    ]
    _BUYER_KEYWORDS = [
        r'(?m)^BUYER["“”]?\s*\)',   # dotloop: ___ ("BUYER")
        r'Buyer\s*(?:Name)?\s*:',
        r'Purchaser\s*(?:Name)?\s*:',
    ]
    _SELLER_KEYWORDS = [
        r'SELLER["“”]?\s*\)',        # dotloop: ___ ("SELLER")
        r'Seller\s*(?:Name)?\s*:',
        r'Vendor\s*(?:Name)?\s*:',
    ]
    _CLOSING_DATE_KEYWORDS = [
        r'Closing\s+Date\s*:',
        r'Close\s+of\s+Escrow\s*(?:Date)?\s*:',
        r'Settlement\s+Date\s*:',
        r'title\s+shall\s+transfer\s+(?:from\s+SELLER\s+to\s+BUYER\s+)?on\s+or\s+about',
    ]
    _EARNEST_KEYWORDS = [
        r'Earnest\s+Money\s*(?:Deposit|Amount|EMD)?\s*:',
        r'EMD\s*:',
        r'Initial\s+(?:Earnest\s+)?Deposit\s*:',
    ]
    _PRICE_KEYWORDS = [
        r'PRICE\s*:\s*BUYER\s+shall\s+pay\s+the\s+following\s+sum\s+of',
        r'Purchase\s+Price\s*:',
        r'Sales?\s+Price\s*:',
        r'sum\s+of\s+\$',
    ]

    def _strip_boilerplate(val: str) -> str:
        """Return empty string if value is obviously form boilerplate."""
        if not val:
            return ""
        vl = val.lower().strip()
        # Blank form line
        if re.match(r'^_+$', val):
            return ""
        # Known form titles / role labels
        if vl in _FORM_TITLES or vl in ('buyer', 'seller', 'agent', 'broker', 'n/a', 'none',
                                          'tbd', 'set', 'date', 'name', 'signature'):
            return ""
        # Any value containing "signature" or "initials" is a signature line, not a name
        if re.search(r'\b(?:signature|initials?)\b', vl):
            return ""
        # Section numbers / form text like "3.1 Buyer will pay..."
        if re.match(r'^\d+\.\d+\s', val):
            return ""
        # Form paragraph text (long sentence starting with paragraph-like words)
        if re.match(r'^(?:buyer\s+will\s+pay|paragraph|the\s+parties|made\s+by|'
                    r'endorsement\s+as|subject\s+to|this\s+contract|pursuant\s+to)', vl):
            return ""
        # All-caps multi-word form header (e.g. "REAL ESTATE PURCHASE CONTRACT")
        if val.isupper() and len(val) > 8 and ' ' in val and not re.search(r'\d', val):
            return ""
        # Long run-on sentence fragments (clearly body text, not a name/company)
        if len(val) > 80 and re.search(r'\b(?:shall|will|the|and|to|of|in|for|is|are|was|were)\b', vl):
            return ""
        return val

    # ── MLS block extraction: Ohio dotloop and similar forms ──────────────────
    # In these PDFs the MLS section has labels in parens like (Listing Agent Name)
    # followed by the actual data as a block after the last template line number.
    # Strategy: find the MLS label sequence, then grab the data lines that follow
    # the last line number in the section.

    def _strip_license(s: str) -> str:
        return re.sub(r'\s+\d{4,}\s*(?:and\s+\d+)?\s*$', '', s).strip()

    # Find the MLS section (identified by any of these anchors)
    _mls_section_m = re.search(
        r'(?:Multiple\s+Listing\s+(?:Service\s+)?Information'
        r'|\(Listing\s+Agent\s+Name\)'
        r'|\(Selling\s+Agent\s+Name\))',
        text, re.IGNORECASE
    )
    if _mls_section_m:
        _mls_block = text[_mls_section_m.start():]
        # Find the last template line number in the MLS block
        # (template lines end with " NNN" where NNN is 3 digits)
        _last_tmpl_m = None
        for _tm in re.finditer(r'\s+(\d{3})\s*\n', _mls_block):
            _last_tmpl_m = _tm
        if _last_tmpl_m:
            _data_block = _mls_block[_last_tmpl_m.end():]
        else:
            # No template line found — take everything after the section header
            _data_block = _mls_block[200:]  # skip header text

        # Split data block into clean lines
        _data_lines = []
        for _dl in _data_block.split('\n'):
            _dl = _dl.strip()
            if not _dl or _is_template_line(_dl):
                continue
            # Strip dotloop verification suffix
            _dl = re.split(r'dotloop\s+(?:signature|verified)', _dl, flags=re.IGNORECASE)[0].strip()
            if _dl:
                _data_lines.append(_dl)

        # The Ohio REALTORS dotloop MLS data block order is:
        # Line 0: listing agent name + phone + email(s)
        # Line 1: listing agent name + license number(s)  [sometimes same as line 0]
        # Line 2: listing brokerage + license
        # Line 3: selling agent + license
        # Line 4: selling brokerage + license
        if len(_data_lines) >= 1:
            _mls0 = _data_lines[0]
            if not listing_agent:
                _nm = _kv_name_only(_mls0)
                _nm = _strip_boilerplate(_nm)
                if _nm and len(_nm) > 2 and '$' not in _nm and not _nm.startswith('('):
                    listing_agent = _nm
            if not listing_phone:
                listing_phone = _kv_phone(_mls0)
            if not listing_email:
                listing_email = _kv_email(_mls0)

        # Find where brokerage/selling agent data starts
        # (skip lines that repeat the listing agent name or are license-only)
        _mls_remaining = _data_lines[1:] if len(_data_lines) > 1 else []
        # Skip lines that are just a repeat of listing agent name + license
        _brokerage_lines = []
        for _rl in _mls_remaining:
            _rl_clean = _strip_license(_rl)
            # If line is only digits/license-like, skip
            if re.match(r'^[\d\s]+(?:and\s+\d+)?$', _rl_clean):
                continue
            # If nearly identical to listing agent (same person repeat), skip
            if listing_agent and _rl_clean.lower().startswith(listing_agent.lower()[:10]):
                continue
            _brokerage_lines.append(_rl)

        if len(_brokerage_lines) >= 1 and not listing_brokerage:
            _co = _strip_boilerplate(_strip_license(_brokerage_lines[0]))
            if _co and len(_co) > 3 and '$' not in _co and not _co.startswith('('):
                listing_brokerage = _co

        if len(_brokerage_lines) >= 2 and not selling_agent:
            _nm = _kv_name_only(_brokerage_lines[1])
            _nm = _strip_boilerplate(_nm)
            if _nm and len(_nm) > 2 and '$' not in _nm and not _nm.startswith('('):
                selling_agent = _nm

        if len(_brokerage_lines) >= 3 and not selling_brokerage:
            _co = _strip_boilerplate(_strip_license(_brokerage_lines[2]))
            if _co and len(_co) > 3 and '$' not in _co and not _co.startswith('('):
                # Strip any appended dotloop text
                _co = re.split(r'dotloop\s+signature', _co, flags=re.IGNORECASE)[0].strip()
                if _co:
                    selling_brokerage = _co

    # ── Keyword extraction: inline-labeled contracts (non-dotloop / other states) ─
    # For any fields still missing, scan for explicit "Keyword: Value" patterns.
    # Only runs if MLS block extraction above didn't already fill the field.

    _KW_FIELDS = [
        # (keyword_patterns, field_getter)
        (_LISTING_AGENT_KEYWORDS,    'listing_agent'),
        (_LISTING_BROKERAGE_KEYWORDS,'listing_brokerage'),
        (_SELLING_AGENT_KEYWORDS,    'selling_agent'),
        (_SELLING_BROKERAGE_KEYWORDS,'selling_brokerage'),
        (_TITLE_KEYWORDS,            'title_company'),
        (_BUYER_KEYWORDS,            'buyer_name'),
        (_SELLER_KEYWORDS,           'seller_name'),
    ]

    _locals = locals()

    for _kws, _fname in _KW_FIELDS:
        if _locals.get(_fname):
            continue  # already filled
        for _kw in _kws:
            _raw = _kv_next(_kw)
            if not _raw:
                continue
            if _fname in ('listing_agent', 'selling_agent', 'buyer_name', 'seller_name'):
                _nm = _strip_boilerplate(_kv_name_only(_raw))
                if _nm and len(_nm) > 2 and '$' not in _nm:
                    _locals[_fname] = _nm
                    # Also try to capture phone/email from same raw line
                    if _fname == 'listing_agent':
                        if not listing_phone: listing_phone = _kv_phone(_raw)
                        if not listing_email: listing_email = _kv_email(_raw)
                    elif _fname == 'selling_agent':
                        if not selling_phone: selling_phone = _kv_phone(_raw)
                        if not selling_email: selling_email = _kv_email(_raw)
                    break
            else:
                _co = _strip_boilerplate(_kv_name_only(_raw))
                if _co and len(_co) > 3 and '$' not in _co:
                    _locals[_fname] = _co
                    break

    # Re-read locals that may have been updated
    listing_agent    = _locals.get('listing_agent', listing_agent)
    listing_brokerage= _locals.get('listing_brokerage', listing_brokerage)
    selling_agent    = _locals.get('selling_agent', selling_agent)
    selling_brokerage= _locals.get('selling_brokerage', selling_brokerage)
    title_company    = _locals.get('title_company', title_company)
    buyer_name       = _locals.get('buyer_name', buyer_name)
    seller_name      = _locals.get('seller_name', seller_name)

    # ── Inline Tel/Email for agents ───────────────────────────────────────────
    # "Listing Agent: ___ Tel.: NNN-NNN-NNNN Email: xxx@yyy.com" (filled by dotloop)
    _la_line_m = re.search(
        r'Listing\s+Agent.*?Tel\.?[:\s]+([\d\-\.\s\(\)]{10,20})\s+Email[:\s]+([\w\.\+\-]+@\S+)',
        text, re.IGNORECASE | re.DOTALL
    )
    if _la_line_m:
        if not listing_phone:
            listing_phone = _la_line_m.group(1).strip()
        if not listing_email:
            listing_email = _la_line_m.group(2).strip()

    _sa_line_m = re.search(
        r'Selling\s+Agent.*?Tel\.?[:\s]+([\d\-\.\s\(\)]{10,20})\s+Email[:\s]+([\w\.\+\-]+@\S+)',
        text, re.IGNORECASE | re.DOTALL
    )
    if _sa_line_m:
        if not selling_phone:
            selling_phone = _sa_line_m.group(1).strip()
        if not selling_email:
            selling_email = _sa_line_m.group(2).strip()

    # ── Key Dates ─────────────────────────────────────────────────────────────
    date_signed = _find([
        r"(?:Date\s+(?:of\s+)?(?:Signing|Signed|Execution|Acceptance)|Accepted\s+(?:on|by)[:\s]+)([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?:Seller\s+(?:Accept|Sign)(?:ed|ance)[:\s]+)([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?:Date\s+of\s+(?:this\s+)?(?:Agreement|Contract|Offer))[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?:Executed|Signed|Dated)\s+(?:this\s+)?(?:\d+(?:st|nd|rd|th)?\s+day\s+of\s+)?([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?:Offer\s+(?:Date|Made|Submitted))[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    ])

    obligation_date = _find([
        r"(?:Loan\s+(?:Approval|Obligation|Commitment)\s+(?:Date|Deadline|Period)|Finance\s+(?:Approval|Contingency)\s+(?:Date|Deadline))[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?:financing\s+(?:must\s+be\s+)?(?:approved|committed|secured)\s+(?:by|no\s+later\s+than))[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?:Buyer\s+(?:must|shall)\s+(?:obtain|secure|receive)\s+(?:loan|mortgage|financing)\s+(?:approval|commitment)\s+(?:by|no\s+later\s+than))[:\s]*([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?:Mortgage\s+Commitment\s+(?:Date|Deadline)|Commitment\s+(?:Date|Deadline))[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?:obligation\s+date|date\s+of\s+obligation)[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
    ])

    # ── Contingencies ─────────────────────────────────────────────────────────
    inspection_days = _find([
        r"(?:Inspection\s*(?:Period|Contingency|Days?))[:\s]+(\d+\s*(?:calendar|business)?\s*days?[^\n]{0,50})",
        r"(\d+)\s*(?:calendar|business)?\s*days?\s+(?:to|for)\s+(?:complete\s+)?inspect",
        r"inspection\s+contingency[:\s]+(\d+[^\n]{0,50})",
    ])
    appraisal_contingency = _find([
        r"(?:Appraisal\s*(?:Contingency|Condition|Clause|Deadline))[:\s]+([^\n_]{3,80})",
        r"subject\s+to\s+(?:an?\s+)?appraisal\s*(?:of\s+not\s+less\s+than)?\s*([^\n_]{3,60})",
        r"property\s+must\s+appraise\s+(?:at|for)[^\n]{0,60}",
    ])
    financing_contingency = _find([
        r"(?:Financing\s*(?:Contingency|Condition|Clause|Deadline)|Loan\s*Contingency)[:\s]+([^\n_]{3,80})",
        r"(?:conditioned?\s+upon|subject\s+to)\s+(?:Buyer\s+)?obtaining\s+(?:a\s+)?(?:loan|mortgage|financing)[^\n_]{0,60}",
        r"Buyer\s+obtaining\s+(?:a\s+)?(?:conventional|FHA|VA|USDA)?\s*(?:loan|mortgage|financing)[^\n_]{0,60}",
    ])

    # ── Addendums — filter out page references and junk ───────────────────────
    addendums_raw = re.findall(
        r"(?:Addendum|Rider|Exhibit|Amendment|Attachment)\s*[:\-#]?\s*([A-Z][^\n]{2,80})",
        text, re.IGNORECASE,
    )
    addendums = []
    for a in addendums_raw:
        a = a.strip()
        # Skip pure page references: "to Purchase 167", "to Agreement 45"
        if re.match(r'^to\s+(?:Purchase|Agreement|Contract|Sale)\b', a, re.IGNORECASE):
            continue
        # Skip fragments from boilerplate: "s and addenda, shall"
        if re.match(r'^[a-z]', a):
            continue
        # Skip if ends with just a standalone number after stripping
        a = re.sub(r'\s+\d{1,3}\s*$', '', a).strip()
        # Skip if too short or all punctuation
        if len(a) < 6 or re.match(r'^[\W\d]+$', a):
            continue
        # Skip if mostly underscores
        if a.count('_') > len(a) * 0.25:
            continue
        # Skip fragments that look like mid-sentence text (no capital start after cleaning)
        if not re.match(r'^[A-Z□☐✓✔☑]', a):
            continue
        # Skip if it's just boilerplate text from the form template
        if re.search(r'(?:shall|herein|thereof|pursuant|notwithstanding)\s', a, re.IGNORECASE) and len(a) > 40:
            continue
        addendums.append(a)
    addendums = list(dict.fromkeys(addendums[:12]))

    # ═══════════════════════════════════════════════════════════════════════════
    # SMART FALLBACK — Structural extraction for dotloop / DocuSign / any form
    # ═══════════════════════════════════════════════════════════════════════════
    # When labeled patterns fail, analyze the raw document structure.
    # Digital-signature PDFs (dotloop, DocuSign, Skyslope) put filled values
    # at the BOTTOM of each page as a data blob.  We extract those blobs,
    # classify each line, and fill whatever the labeled patterns missed.

    # Step 1: Split pages.  Dotloop pages end with "dotloop signature verification:"
    # Other PDFs may have form-feed chars or "Page X of Y".
    _pages = re.split(r'(?:dotloop\s+signature\s+verification[^\n]*\n?)+', text)
    if len(_pages) < 2:
        _pages = re.split(r'\f', text)  # try form-feed split

    # Step 2: For each page, extract the "data blob" — lines after the last
    # numbered form line (e.g. "...some text 45\n") or after template text.
    _all_blob_lines = []
    for _page in _pages:
        _page = _page.strip()
        if not _page:
            continue
        _lines = _page.split('\n')
        # Find where the form template text ends.
        # Template lines end with a line number like "  45" or " 298".
        _last_template_idx = -1
        for _li, _line in enumerate(_lines):
            _stripped = _line.rstrip()
            # Template line: ends with a number that could be a line reference
            if re.search(r'\s+\d{1,3}\s*$', _stripped) and len(_stripped) > 20:
                _last_template_idx = _li
            # Also: lines that are mostly underscores are template
            elif _stripped.count('_') > len(_stripped) * 0.4 and len(_stripped) > 10:
                _last_template_idx = _li

        # Data blob = everything after the last template line
        if _last_template_idx >= 0 and _last_template_idx < len(_lines) - 1:
            _blob = _lines[_last_template_idx + 1:]
        else:
            # If no clear template boundary, take last few non-empty lines
            _blob = [l for l in _lines[-8:] if l.strip()]

        for _bl in _blob:
            _bl = _bl.strip()
            if not _bl:
                continue
            # Skip dotloop metadata
            if re.match(r'^(dotloop|dtlp\.us|[A-Z0-9]{4}-[A-Z0-9]{4})', _bl):
                continue
            if _bl.lower().startswith('dotloop'):
                continue
            # Skip timestamps like "02/14/22 9:53 AM EST"
            if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}', _bl):
                continue
            # Skip "dotloop verified" or just initials
            if _bl == 'dotloop verified' or (len(_bl) <= 3 and _bl.isupper()):
                continue
            _all_blob_lines.append(_bl)

    # Step 3: Classify each blob line
    _blob_names = []      # likely person names
    _blob_addresses = []  # likely street addresses
    _blob_prices = []     # likely dollar amounts
    _blob_dates = []      # likely dates
    _blob_companies = []  # likely company names (contains Title, Escrow, Realty, etc.)
    _blob_phones = []     # phone numbers
    _blob_emails = []     # emails

    _COMPANY_WORDS = {'title', 'escrow', 'realty', 'remax', 're/max', 'keller',
                      'coldwell', 'century', 'sotheby', 'berkshire', 'compass',
                      'exp ', 'eXp', 'howard', 'hanna', 'traditions', 'living',
                      'settlement', 'abstract', 'land ', 'closing', 'national'}

    for _bl in _all_blob_lines:
        _bl_clean = _clean(_bl)
        if not _bl_clean:
            continue

        # Email
        _em_m = re.search(r'([\w\.\+\-]+@[\w\.\-]+\.\w{2,})', _bl)
        if _em_m:
            _blob_emails.append(_em_m.group(1))

        # Phone
        _ph_m = re.search(r'(\d{3}[\-\.\s]\d{3}[\-\.\s]\d{4})', _bl)
        if _ph_m:
            _blob_phones.append(_ph_m.group(1))

        # Date (MM/DD/YYYY or MM/DD/YY)
        _dt_m = re.match(r'^(\d{1,2}/\d{1,2}/\d{4})\s*(?:\d{1,2}/\d{1,2}/\d{4})?\s*$', _bl)
        if _dt_m:
            _blob_dates.append(_dt_m.group(1))
            continue

        # Price: standalone number >= $1,000 (digits + commas + optional decimal)
        _pr_m = re.match(r'^[\$]?\s*([\d]{1,3}(?:,\d{3})+(?:\.\d{2})?)\s*$', _bl)
        if _pr_m:
            try:
                _val = float(_pr_m.group(1).replace(',', ''))
                if _val >= 1000:
                    _blob_prices.append((_val, _pr_m.group(1)))
            except ValueError:
                pass
            continue

        # Address: starts with digit, contains street-type words or city,state pattern
        if re.match(r'^\d{1,6}\s+[A-Z]', _bl_clean):
            _blob_addresses.append(_bl_clean)
            continue

        # Company: contains a known real estate / title keyword
        _bl_lower = _bl_clean.lower()
        if any(kw in _bl_lower for kw in _COMPANY_WORDS):
            # Strip trailing license numbers
            _co = re.sub(r'\s+\d{4,}\s*(?:and\s+\d+)?\s*$', '', _bl_clean).strip()
            # Reject section headers like "Selling Brokerage:" or "Listing Brokerage:"
            if re.match(r'^(?:selling|listing|buyer|seller)\s*(?:brokerage|office|agent|name)?:', _bl_lower):
                continue
            if _co and len(_co) > 3:
                _blob_companies.append(_co)
            continue

        # Name: 2-5 capitalized words, no digits (except for " and " connector)
        # Strip trailing license numbers first
        _name_candidate = re.sub(r'\s+\d{4,}\s*(?:and\s+\d+)?\s*$', '', _bl_clean).strip()
        # Strip phone/email from end
        _name_candidate = re.sub(r'\s+\d{3}[\-\.\s]\d{3}[\-\.\s]\d{4}.*$', '', _name_candidate).strip()
        _name_candidate = re.sub(r'\s+[\w\.\+\-]+@\S+.*$', '', _name_candidate).strip()

        if (re.match(r'^[A-Z][a-zA-Z\'\-]+(?:\s+(?:and\s+)?[A-Z][a-zA-Z\'\-]+){0,5}$', _name_candidate)
                and len(_name_candidate) > 3
                and not _name_candidate.startswith('(')
                and _name_candidate.lower() not in _ROLE_LABELS):
            # Skip known junk
            _nl = _name_candidate.lower()
            if not any(_nl.startswith(j) for j in ['as specified', 'will ', 'shall ', 'herein',
                                                     'agent', 'broker', 'represent', 'the buyer',
                                                     'the seller', 'see attached', 'none',
                                                     'remainder', 'conventional', 'cash']):
                _blob_names.append(_name_candidate)

    # Step 4: Fill blanks using classified blob data
    # Names: first appearance = buyer, second = seller (in Agency Disclosure / first page)
    if not buyer_name and _blob_names:
        buyer_name = _blob_names[0]
    if not seller_name and len(_blob_names) >= 2:
        # Seller is the first name that isn't the buyer
        for _n in _blob_names[1:]:
            if _n != buyer_name and _n.upper() != buyer_name.upper():
                seller_name = _n
                break

    # Address: first address found
    if not property_address and _blob_addresses:
        property_address = _blob_addresses[0]

    # Price: largest amount >= $50k
    if not purchase_price and _blob_prices:
        _big_prices = [(v, s) for v, s in _blob_prices if v >= 50000]
        if _big_prices:
            _big_prices.sort(key=lambda x: x[0], reverse=True)
            _val, _str = _big_prices[0]
            purchase_price = f"{_val:,.0f}" if _val == int(_val) else f"{_val:,.2f}"

    # Earnest money: smallest amount >= $100 that isn't the purchase price
    if not earnest_money and _blob_prices:
        _small = [(v, s) for v, s in _blob_prices if v >= 100 and (not purchase_price or str(int(v)) not in purchase_price.replace(',', ''))]
        if _small:
            _small.sort(key=lambda x: x[0])
            _val, _str = _small[0]
            earnest_money = f"{_val:,.0f}" if _val == int(_val) else f"{_val:,.2f}"

    # Closing date: first date found (dotloop puts it after title company)
    if not closing_date and _blob_dates:
        closing_date = _blob_dates[0]

    # Title company
    if not title_company and _blob_companies:
        for _co in _blob_companies:
            _cl = _co.lower()
            if 'title' in _cl or 'escrow' in _cl or 'settlement' in _cl:
                title_company = _co
                break

    # Agent / brokerage from blob names + companies (if MLS block didn't find them)
    # Agents are typically the 3rd+ names in the blob (after buyer + seller)
    _remaining_names = [n for n in _blob_names if n != buyer_name and n != seller_name]
    _remaining_companies = [c for c in _blob_companies if c != title_company]

    if not listing_agent and _remaining_names:
        listing_agent = _remaining_names[0]
    if not selling_agent and len(_remaining_names) >= 2:
        selling_agent = _remaining_names[1]

    if not listing_brokerage and _remaining_companies:
        listing_brokerage = _remaining_companies[0]
    if not selling_brokerage and len(_remaining_companies) >= 2:
        selling_brokerage = _remaining_companies[1]

    # Phone/email from blobs (assign to listing agent if not yet set)
    if not listing_phone and _blob_phones:
        listing_phone = _blob_phones[0]
    if not listing_email and _blob_emails:
        listing_email = _blob_emails[0]

    # ── Missing required fields check ─────────────────────────────────────────
    required = {
        "Buyer Name":        buyer_name,
        "Seller Name":       seller_name,
        "Property Address":  property_address,
        "Purchase Price":    purchase_price,
        "Closing Date":      closing_date,
    }
    missing = [k for k, v in required.items() if not v]

    return {
        "buyer":   {"name": buyer_name,   "phone": buyer_phone,   "email": buyer_email},
        "seller":  {"name": seller_name,  "phone": seller_phone,  "email": seller_email},
        "property":{"address": property_address},
        "transaction": {
            "purchase_price":     purchase_price,
            "closing_date":       closing_date,
            "date_signed":        date_signed,
            "obligation_date":    obligation_date,
            "earnest_money":      earnest_money,
            "down_payment":       down_payment,
            "seller_concessions": seller_concessions,
        },
        "listing_agent": {
            "name":      listing_agent,
            "brokerage": listing_brokerage,
            "phone":     listing_phone,
            "email":     listing_email,
        },
        "selling_agent": {
            "name":      selling_agent,
            "brokerage": selling_brokerage,
            "phone":     selling_phone,
            "email":     selling_email,
        },
        "title": {
            "company": title_company,
            "contact": title_contact,
            "phone":   title_phone,
            "email":   title_email,
        },
        "contingencies": {
            "inspection": inspection_days,
            "appraisal":  appraisal_contingency,
            "financing":  financing_contingency,
        },
        "addendums":       addendums,
        "missing_required":missing,
    }


# ---------------------------------------------------------------------------
# Document Type Auto-Detection
# ---------------------------------------------------------------------------

def detect_doc_type(pdf_bytes: bytes) -> dict:
    """
    Auto-detect the document type from PDF content.
    Reads only the first 2 pages for speed.
    Returns {"doc_type": str, "confidence": str, "signals": list[str]}.
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages[:2]:
            text += (page.extract_text() or "") + "\n"
    except Exception:
        return {"doc_type": "Unknown", "confidence": "None", "signals": ["Could not read PDF"]}

    if len(text.strip()) < 30:
        return {"doc_type": "Unknown", "confidence": "None", "signals": ["No readable text"]}

    t = text.lower()

    # Ordered by specificity — most distinctive patterns first
    _RULES = [
        # 1003 / URLA
        ("1003 Application", [
            (r'uniform\s*residential\s*loan\s*application', 40),
            (r'\b1003\b', 25),
            (r'borrower\s*information.*co[\s-]*borrower', 20),
            (r'assets\s*and\s*liabilities', 15),
            (r'declarations?\s.*(?:outstanding\s*judgments|bankrupt)', 15),
            (r'present\s*address.*(?:own|rent)', 12),
            (r'gross\s*monthly\s*income', 12),
        ]),
        # Closing Disclosure
        ("Closing Disclosure (CD)", [
            (r'closing\s*disclosure', 50),
            (r'closing\s*cost\s*details', 25),
            (r'loan\s*terms.*projected\s*payments', 20),
            (r'cash\s*to\s*close', 15),
            (r'origination\s*charges', 10),
        ]),
        # Loan Estimate
        ("Loan Estimate (LE)", [
            (r'loan\s*estimate', 50),
            (r'estimated\s*(?:closing\s*costs|total)', 20),
            (r'projected\s*payments', 15),
            (r'comparisons?\s*.*(?:other\s*loans|apr)', 10),
        ]),
        # Credit Report
        ("Credit Report", [
            (r'(?:credit\s*report|credit\s*file)', 30),
            (r'tri[\s-]*merge', 35),
            (r'(?:fico|score)\s*\d{3}', 25),
            (r'(?:equifax|experian|transunion)', 20),
            (r'trade\s*line|revolving|installment', 12),
            (r'(?:collection|charge[\s-]*off|derog)', 10),
        ]),
        # Bank Statement
        ("Bank Statement", [
            (r'(?:bank\s*statement|account\s*statement)', 35),
            (r'(?:statement\s*period|beginning\s*balance|ending\s*balance)', 30),
            (r'account\s*(?:number|summary|activity)', 20),
            (r'(?:deposits?\s*and|checks?\s*and|withdrawals?)', 15),
            (r'(?:available\s*balance|ledger\s*balance)', 12),
        ]),
        # Purchase Contract
        ("Purchase Contract", [
            (r'(?:purchase\s*(?:and\s*sale\s*)?(?:agreement|contract))', 60),
            (r'(?:buyer|purchaser)\s*(?:and|&)\s*(?:seller|vendor)', 50),
            (r'(?:seller|vendor)\s*(?:and|&)\s*(?:buyer|purchaser)', 50),
            (r'earnest\s*money', 50),
            (r'(?:real\s*estate|property)\s*(?:contract|agreement|purchase)', 40),
            (r'(?:closing\s*date|settlement\s*date).*(?:escrow|title)', 35),
            (r'inspection\s*(?:period|contingency)', 40),
            (r'financing\s*(?:period|contingency)', 40),
            (r'seller\s*concession', 40),
            (r'purchase\s*price', 45),
            (r'mls\s*number', 30),
            (r'(?:title\s*company|escrow\s*company)', 35),
            (r'(?:listing\s*agent|selling\s*agent)', 40),
        ]),
        # Approval / Commitment Letter (merged — includes AUS findings)
        ("Approval Letter", [
            (r'(?:approv(?:al|ed)\s*(?:letter|notification|notice))', 50),
            (r'commitment\s*letter', 50),
            (r'(?:conditional(?:ly)?\s*approv)', 45),
            (r'(?:this\s*loan\s*(?:has\s*been|is)\s*approved)', 55),
            (r'(?:subject\s*to\s*the\s*following\s*conditions?)', 45),
            (r'(?:cleared?\s*to\s*close|clear\s*to\s*close|\bctc\b)', 40),
            (r'(?:prior[\s-]*to[\s-]*(?:closing|funding|docs?)\s*condition)', 40),
            # Common wholesaler condition-category labels — very decisive
            (r'\bprior\s*to\s*docs?\b', 45),
            (r'\bprior\s*to\s*funding\b', 45),
            (r'\bprior\s*to\s*closing\b', 40),
            (r'\bptd\s*conditions?\b', 40),
            (r'\bptf\s*conditions?\b', 40),
            # Orion/AFN-style and generic "LOAN DECISION" header
            (r'\bloan\s*decision\b', 60),
            (r'\bcredit\s*decision\b', 45),
            (r'\bunderwriting\s*decision\b', 45),
            (r'\buw\s*decision\b', 40),
            (r'\bloan\s*approval\b', 50),
            (r'\bloan\s*conditions?\b', 45),
            (r'(?:loan\s*conditions?|conditions?\s*(?:of\s*approval|list|summary))', 35),
            (r'(?:conditions?\s*(?:prior\s*to|to\s*be\s*(?:satisfied|met|cleared)))', 30),
            (r'(?:underwrit(?:ing|er)\s*(?:decision|conditions?|approval))', 30),
            (r'(?:broker\s*copy|lender\s*copy).*(?:conditions?|approval)', 25),
            # AUS findings (formerly a second Approval Letter entry)
            (r'(?:desktop\s*underwriter|du\s*findings?|du\s*approve[d]?)', 60),
            (r'(?:loan\s*prospector|lpa\s*findings?|freddie\s*mac\s*findings?)', 60),
            (r'(?:approve[d]?/eligible|approve[d]?/ineligible|refer\s*with\s*caution)', 50),
            (r'(?:fannie\s*mae\s*(?:approval|approve|findings?)|fnma\s*findings?)', 50),
            (r'(?:underwriting\s*findings?|aus\s*findings?)', 35),
            (r'(?:maximum\s*loan\s*amount|qualifying\s*ratio|dti\s*ratio)', 20),
            # Generic phrasing that shows up on wholesaler approvals w/o AUS language
            (r'(?:pre[\s-]*approval|pre[\s-]*qual(?:ification)?)', 30),
            (r'(?:approval\s*summary|approval\s*notice)', 35),
            # Condition-row structure: "Responsible # Status Date Description"
            # or a condition grid with Underwriter/Broker/Other party columns
            (r'responsible\s*#?\s*status\s*(?:date\s*)?description', 50),
            (r'(?:senior\s*underwriter|account\s*executive|account\s*manager)\s*:', 35),
            (r'(?:expiration\s*dates|closing\s*made\s*simple)', 30),
            (r'(?:borrower(?:\(s\))?\s*(?:name|information)[\s\S]{0,200}?'
             r'(?:loan\s*(?:amount|number|program|type)))', 20),
        ]),
        # Change of Circumstance
        ("Change of Circumstance (COC)", [
            (r'(?:change\s*of\s*circumstance|changed\s*circumstance)', 50),
            (r'(?:revised?\s*loan\s*estimate)', 30),
            (r'(?:reason\s*for\s*(?:change|revision))', 20),
        ]),
        # Broker Package
        ("Broker Package (BP)", [
            (r'(?:broker\s*(?:package|submission|transmittal))', 40),
            (r'(?:wholesale\s*(?:submission|lending))', 25),
            (r'(?:tpo|third[\s-]*party\s*originator)', 20),
        ]),
        # Pay Stub
        ("Pay Stub", [
            (r'(?:pay\s*(?:stub|statement|advice|check))', 35),
            (r'(?:gross\s*pay|net\s*pay|ytd)', 25),
            (r'(?:federal\s*tax|fica|social\s*security)', 15),
            (r'(?:employer|employee).*(?:pay\s*period|hours)', 12),
        ]),
        # W-2
        ("W-2", [
            (r'(?:wage\s*and\s*tax\s*statement)', 50),
            (r'\bw[\s-]*2\b', 30),
            (r'(?:employer.*identification|ein)', 15),
            (r'(?:federal\s*income\s*tax\s*withheld)', 20),
        ]),
        # Tax Return
        ("Tax Return", [
            (r'(?:form\s*1040|u\.?s\.?\s*individual\s*income\s*tax)', 40),
            (r'(?:schedule\s*[a-e]|adjusted\s*gross\s*income)', 20),
            (r'(?:internal\s*revenue\s*service|irs)', 15),
            (r'(?:tax\s*(?:return|year)\s*\d{4})', 20),
        ]),
        # 1099
        ("1099", [
            (r'\b1099[-\s]?(?:NEC|MISC|INT|DIV|R|G|K|S|C|B|OID|PATR|Q|SA|LTC|A|H|LS|SB)\b', 60),
            (r'\b1099\b', 40),
            (r'(?:nonemployee\s*compensation|non-employee\s*compensation)', 40),
            (r'(?:payer.{0,20}(?:name|tin|id))', 25),
            (r'(?:recipient.{0,20}(?:name|tin|ssn))', 25),
            (r'(?:miscellaneous\s*(?:income|information)|rents|royalties)', 20),
            (r'(?:omb\s*no\.?\s*1545-00(?:96|98|99|15|16|17|19|20|21|22))', 25),
        ]),
        # Credit Report
        ("Credit Report", [
            (r'(?:residential\s*mortgage\s*credit\s*report|rmcr)', 60),
            (r'(?:credit\s*report|consumer\s*credit\s*report|tri[\s-]?merge)', 50),
            (r'(?:experian|equifax|transunion|trans\s*union)', 35),
            (r'(?:fico\s*score|credit\s*score|vantage\s*score|beacon\s*score)', 35),
            (r'(?:xactus|advantage\s*credit|factual\s*data|corelogic|credco|sarma|cbcinnovis)', 50),
            (r'(?:derogatory|delinquency|charge[\s-]?off|collection)', 25),
            (r'(?:revolving|installment|open\s*account)', 20),
            (r'(?:inquiry|inquiries)', 20),
            (r'(?:public\s*record)', 20),
            (r'(?:payment\s*history|credit\s*limit|high\s*balance|past\s*due)', 15),
            (r'(?:account\s*(?:type|status|number)|creditor\s*name)', 15),
        ]),
        # Appraisal
        ("Appraisal", [
            (r'(?:appraisal\s*report|uniform\s*(?:residential|appraisal))', 40),
            (r'(?:appraised\s*value|market\s*value)', 30),
            (r'(?:comparable\s*(?:sale|property))', 25),
            (r'(?:subject\s*property|improvements?.*(?:sqft|sq\s*ft))', 15),
        ]),
        # Title Commitment
        ("Title Commitment", [
            (r'(?:title\s*(?:commitment|insurance|policy))', 35),
            (r'(?:schedule\s*[ab]|exceptions?.*(?:title|lien))', 20),
            (r'(?:legal\s*description|vesting)', 15),
        ]),
        # Mortgage Statement
        ("Mortgage Statement", [
            (r'(?:mortgage\s*statement|loan\s*statement)', 50),
            (r'(?:principal\s*balance|escrow\s*balance|amount\s*due)', 30),
            (r'(?:payment\s*due\s*date|next\s*payment|current\s*payment)', 25),
            (r'(?:servicer|loan\s*servic)', 20),
        ]),
        # VA / Military Docs
        ("VA Certificate of Eligibility", [
            (r'(?:certificate\s*of\s*eligibility)', 70),
            (r'(?:entitlement\s*(?:code|amount|charged|remaining|available))', 50),
            (r'(?:loan\s*guaranty\s*(?:amount|certificate|issued))', 45),
            (r'(?:remaining\s*entitlement|basic\s*entitlement)', 40),
            (r'(?:veterans?\s*administration|department\s*of\s*veterans?\s*affairs)', 20),
            (r'(?:surviving\s*spouse)', 20),
            (r'(?:funding\s*fee\s*(?:exempt|exemption|waived))', 15),
            # Negative: AUS/underwriting docs are NOT COEs
            (r'(?:desktop\s*underwriter|du\s*findings?|approve[d]?/eligible|aus\s*findings?|loan\s*prospector|underwriting\s*findings?|dti\s*ratio|qualifying\s*ratio)', -100),
        ]),
        ("DD-214", [
            (r'(?:dd[\s-]?214)', 60),
            (r'(?:certificate\s*of\s*release)', 50),
            (r'(?:discharge\s*from\s*active\s*duty)', 50),
            (r'(?:character\s*of\s*(?:service|discharge))', 40),
            (r'(?:narrative\s*reason\s*for\s*separation)', 40),
            (r'(?:branch\s*of\s*service|type\s*of\s*separation)', 30),
            (r'(?:armed\s*forces|active\s*duty)', 20),
            (r'(?:military\s*service|service\s*member)', 15),
        ]),
        # ID Documents
        ("Government ID", [
            (r'(?:driver.?s?\s*licen[sc]e)', 55),
            (r'(?:state\s*id|identification\s*card)', 50),
            (r'(?:social\s*security\s*card)', 55),
            (r'(?:passport\b)', 50),
            (r'(?:military\s*id|common\s*access\s*card)', 50),
            (r'(?:government[\s-]issued\s*id)', 50),
            (r'(?:expir(?:es?|ation\s*date))', 20),
            (r'(?:date\s*of\s*birth|dob\b)', 15),
            (r'(?:license\s*(?:number|no\.?|class))', 15),
        ]),
        # Hazard / Homeowner's Insurance — boosted standalone
        ("Hazard Insurance", [
            (r'(?:homeowner.?s?\s*insurance\s*(?:policy|declaration|binder))', 60),
            (r'(?:hazard\s*insurance)', 55),
            (r'(?:home.?owners?\s*insurance)', 50),
            (r'(?:declarations?\s*page)', 45),
            (r'(?:named\s*insured)', 40),
            (r'(?:policy\s*(?:number|period|effective))', 30),
            (r'(?:dwelling\s*coverage|liability\s*coverage|personal\s*property)', 25),
            (r'(?:premium\b)', 20),
            (r'(?:deductible\b)', 15),
        ]),
    ]

    best_type = "Unknown"
    best_score = 0
    best_signals = []

    # Strong approval-letter indicators — if present, any non-Approval doc
    # that lacks its own body-tells is almost certainly being *referenced*
    # as a condition inside the approval, not the approval itself.
    _has_approval_signal = any(re.search(p, t) for p in [
        r'this\s*loan\s*(?:has\s*been|is)\s*approved',
        r'subject\s*to\s*the\s*following\s*conditions?',
        r'conditional(?:ly)?\s*approv',
        r'prior[\s-]*to[\s-]*(?:closing|funding|docs?)\s*condition',
        r'loan\s*conditions?\s*(?:list|summary|report)',
        r'(?:du\s*findings?|loan\s*product\s*advisor|\blpa\b)',
        r'(?:cleared?\s*to\s*close|\bctc\b)',
        r'commitment\s*letter',
        # Orion/AFN + generic wholesaler condition-grid approvals
        r'\bloan\s*decision\b',
        r'\bloan\s*approval\b',
        r'\bloan\s*conditions?\b',
        r'\bcredit\s*decision\b',
        r'\bprior\s*to\s*(?:docs?|funding|closing)\b',
        r'\bptd\s*conditions?\b',
        r'responsible\s*#?\s*status\s*(?:date\s*)?description',
        r'(?:senior\s*underwriter|account\s*executive|account\s*manager)\s*:',
    ])

    # Body-tells: phrases that appear ONLY in an actual instance of that
    # doc type, not when the type is merely referenced by name. If a doc
    # scores high for type X but has zero body-tells for X, it's being
    # name-dropped inside another doc.
    _BODY_TELLS = {
        "Hazard Insurance": [
            r'declarations?\s*page', r'policy\s*(?:number|period|effective)',
            r'named\s*insured', r'dwelling\s*coverage', r'coverage\s*(?:a|b|c|d)\b',
        ],
        "Title Commitment": [
            r'commitment\s*(?:effective\s*date|for\s*title\s*insurance|no\.?\s*[A-Z0-9])',
            r'schedule\s*a[\s\S]{0,120}?(?:effective\s*date|proposed\s*insured|amount\s*of\s*insurance)',
            r'schedule\s*b[\s\S]{0,120}?(?:requirements?|exceptions?)',
            r'proposed\s*insured',
            r'(?:title\s*company|title\s*agent|underwriter).{0,60}(?:file\s*(?:no|number)|order\s*(?:no|number))',
        ],
        "Appraisal": [
            r'uniform\s*residential\s*appraisal\s*report', r'\b1004\b',
            r'comparable\s*sale\s*\d', r'subject\s*property\s*(?:address|characteristics)',
            r'reconciliation', r'final\s*(?:opinion\s*of\s*)?value',
            r'sales\s*comparison\s*approach', r'cost\s*approach',
        ],
        "Bank Statement": [
            r'(?:beginning|ending)\s*balance', r'statement\s*period',
            r'deposits?\s*(?:and|&)\s*credits?', r'withdrawals?\s*(?:and|&)\s*debits?',
            r'account\s*summary', r'available\s*balance',
        ],
        "Credit Report": [
            r'(?:experian|equifax|transunion|trans\s*union)',
            r'(?:fico|beacon|vantage)\s*score',
            r'tradeline', r'tri[\s-]*merge',
            r'payment\s*history.*\d{1,3}\s*months',
        ],
        "Pay Stub": [
            r'(?:pay\s*period|pay\s*date)', r'gross\s*pay.*net\s*pay',
            r'ytd\s*(?:gross|earnings|pay)', r'federal\s*(?:income\s*)?tax\s*withheld',
            r'fica|medicare', r'earnings\s*statement',
        ],
        "W-2": [
            r'wage\s*and\s*tax\s*statement', r'employer.{0,30}(?:identification|ein)',
            r'box\s*\d+', r'social\s*security\s*wages',
            r'federal\s*income\s*tax\s*withheld',
        ],
        "Tax Return": [
            r'form\s*1040', r'adjusted\s*gross\s*income',
            r'(?:schedule\s*[a-e]\b).*(?:line|amount)',
            r'taxable\s*income', r'total\s*income.*line\s*\d',
        ],
        "1099": [
            r'\b1099[-\s]?(?:NEC|MISC|INT|DIV|R|G|K|S|C|B|OID|PATR|Q|SA|LTC|A|H|LS|SB)\b',
            r'omb\s*no\.?\s*1545-', r'payer.{0,30}(?:tin|id)',
            r'recipient.{0,30}(?:tin|ssn)',
        ],
        "Mortgage Statement": [
            r'(?:principal\s*balance|unpaid\s*principal)',
            r'escrow\s*(?:balance|summary|activity)',
            r'(?:next\s*payment\s*date|payment\s*due\s*date)',
            r'(?:servicer|loan\s*servic(?:er|ing))',
        ],
        "Purchase Contract": [
            r'purchase\s*(?:and\s*sale\s*)?(?:agreement|contract)',
            r'earnest\s*money',
            r'closing\s*date',
            r'inspection\s*contingency',
            r'financing\s*contingency',
            r'(?:buyer|purchaser)',
            r'(?:seller|vendor)',
            r'real\s*estate',
            r'property\s*address',
        ],
        "Closing Disclosure (CD)": [
            r'closing\s*disclosure', r'projected\s*payments',
            r'cash\s*to\s*close', r'(?:loan\s*terms|origination\s*charges)',
            r'(?:services\s*borrower\s*(?:did|cannot)\s*shop\s*for)',
        ],
        "Loan Estimate (LE)": [
            r'loan\s*estimate(?!\s*(?:required|needed|missing))',
            r'(?:estimated\s*closing\s*costs|estimated\s*total)',
            r'projected\s*payments',
            r'(?:comparisons?|other\s*considerations)',
            r'in\s*5\s*years',
        ],
        "1003 Application": [
            r'uniform\s*residential\s*loan\s*application',
            r'\bform\s*1003\b', r'section\s*[1-9][a-z]?\.\s*',
            r'demographic\s*information\s*(?:addendum|section)',
            r'(?:declarations\s*section|acknowledgments\s*and\s*agreements)',
        ],
        "Government ID": [
            r'driver.?s?\s*licen[sc]e',
            r'state\s*id\s*number',
            r'date\s*of\s*birth',
            r'expir(?:es?|ation)\s*date',
            r'sex\s*:|eye\s*color\s*:|hair\s*color\s*:',
        ],
    }

    _present_body_tells = {
        dt: any(re.search(p, t) for p in pats)
        for dt, pats in _BODY_TELLS.items()
    }

    for doc_type, patterns in _RULES:
        score = 0
        signals = []
        for pat, weight in patterns:
            if re.search(pat, t):
                score += weight
                m = re.search(pat, t)
                if m:
                    signals.append(m.group(0).strip()[:50])
        # Uniform guard: non-Approval types get heavily penalized when the
        # text clearly is an approval (signals present) OR when the type's
        # own body-tells are completely absent.
        if doc_type != "Approval Letter" and doc_type in _BODY_TELLS:
            if _has_approval_signal:
                score = int(score * 0.2)
            if not _present_body_tells.get(doc_type, False):
                score = int(score * 0.3)
        if score > best_score:
            best_score = score
            best_type = doc_type
            best_signals = signals[:3]

    if best_score >= 40:
        confidence = "High"
    elif best_score >= 20:
        confidence = "Medium"
    elif best_score > 0:
        confidence = "Low"
    else:
        confidence = "None"
        best_type = "Unknown"

    return {
        "doc_type": best_type,
        "confidence": confidence,
        "score": best_score,
        "signals": best_signals,
    }


# ---------------------------------------------------------------------------
# Credit Report Parser
# ---------------------------------------------------------------------------

def extract_credit_report(text: str) -> dict:
    """
    Extract structured data from a tri-merge or single-bureau credit report.
    Pulls borrower info, all 3 scores, tradelines, collections, public records.
    100% offline — regex only.
    """
    import re

    def _find(pattern, src, group=1, flags=re.IGNORECASE | re.MULTILINE):
        m = re.search(pattern, src, flags)
        if m:
            try:
                return m.group(group).strip()
            except Exception:
                return ""
        return ""

    def _findall(pattern, src, flags=re.IGNORECASE | re.MULTILINE):
        return re.findall(pattern, src, flags)

    # ── Borrower personal info ─────────────────────────────────────────────
    # Require label followed by colon OR newline, then a real name (not another label word)
    name = _find(r'(?:Borrower|Primary\s*Applicant|Consumer)[:\s]*\n?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})', text)
    if not name:
        # "Borrower: CRYSTAL ROGERS" pattern
        name = _find(r'(?:Borrower|Primary\s*Applicant|Consumer)[:\s]+([A-Z]{2,}(?:\s+[A-Z]{2,}){1,3})\b(?!\s+(?:Name|SSN|Social|Date|Address|Number))', text)
    if not name:
        name = _find(r'^([A-Z][A-Z\-\']{1,}\s+[A-Z][A-Z\-\']{1,}(?:\s+[A-Z][A-Z\-\']{1,})?)\s*$', text, flags=re.MULTILINE)

    ssn = _find(r'(?:SSN|Social\s*Security)[:\s#]*([X\*\d]{3}[-\s][X\*\d]{2}[-\s]\d{4})', text)
    if not ssn:
        ssn = _find(r'\b(\d{3}-\d{2}-\d{4}|XXX-XX-\d{4})\b', text)

    dob = _find(r'(?:DOB|Date\s*of\s*Birth|Birth\s*Date)[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})', text)

    address = _find(r'(?:(?:Current|Present|Mailing)?\s*Address)[:\s]+(\d[^\n]{5,80})', text)
    if not address:
        address = _find(r'(\d{2,6}\s+[A-Z][A-Za-z\s]+(?:ST|AVE|DR|RD|BLVD|WAY|LN|CT|PL|CIR)[,\s]+[A-Z]{2}\s+\d{5})', text)

    employer = _find(r'(?:Employer|Employment)[:\s]+([^\n]{3,60})', text)

    # ── Credit scores ──────────────────────────────────────────────────────
    # Tri-merge reports show all 3. Single bureau shows 1.
    scores = {}

    # Pattern: "Experian: 720" or "EXP 720" or "Equifax 715"
    for bureau, patterns in [
        ("Experian",  [r'Experian[:\s]+(\d{3})', r'\bEXP(?:ERIAN)?[:\s#\-]+(\d{3})\b', r'Experian\s*Score[:\s]+(\d{3})']),
        ("Equifax",   [r'Equifax[:\s]+(\d{3})', r'\bEFX[:\s#\-]+(\d{3})\b', r'Equifax\s*Score[:\s]+(\d{3})']),
        ("TransUnion",[r'Trans\s*Union[:\s]+(\d{3})', r'\bTU[:\s#\-]+(\d{3})\b', r'TransUnion\s*Score[:\s]+(\d{3})']),
    ]:
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                scores[bureau] = int(m.group(1))
                break

    # Fallback: find any 3-digit scores in a scores section
    if not scores:
        score_section = re.search(
            r'(?:FICO|Credit|Score)[s\s]*(?:Summary|Overview)?[:\s]+([\s\S]{0,400})',
            text, re.IGNORECASE
        )
        if score_section:
            found = re.findall(r'\b([5-8]\d{2})\b', score_section.group(1))
            if found:
                labels = ["Experian", "Equifax", "TransUnion"]
                for i, s in enumerate(found[:3]):
                    scores[labels[i]] = int(s)

    # Standalone: any 3-digit score 500-850 near bureau name
    if not scores:
        all_scores = re.findall(r'\b([5-8]\d{2})\b', text)
        if len(all_scores) == 1:
            scores["Score"] = int(all_scores[0])
        elif len(all_scores) >= 3:
            # Take first 3 unique
            unique = []
            for s in all_scores:
                if int(s) not in unique:
                    unique.append(int(s))
                if len(unique) == 3:
                    break
            labels = ["Experian", "Equifax", "TransUnion"]
            for i, s in enumerate(unique[:3]):
                scores[labels[i]] = s

    # Middle score calculation
    middle_score = None
    middle_bureau = None
    if len(scores) == 3:
        sorted_scores = sorted(scores.items(), key=lambda x: x[1])
        middle_bureau, middle_score = sorted_scores[1]
    elif len(scores) == 1:
        middle_bureau, middle_score = list(scores.items())[0]

    # ── Tradelines / accounts ─────────────────────────────────────────────
    # Look for past due, derogatory, collections accounts
    derogatory = []
    derog_patterns = [
        r'(?:COLLECTION|CHARGE[\s\-]?OFF|CHARGE OFF)[^\n]{0,120}',
        r'(?:DEROGATORY|DELINQUENT|PAST\s*DUE)[^\n]{0,120}',
        r'(?:30|60|90|120)\s*(?:DAYS?\s*)?(?:LATE|PAST\s*DUE)[^\n]{0,120}',
        r'(?:REPOSSESSION|FORECLOSURE|BANKRUPTCY)[^\n]{0,120}',
    ]
    for pat in derog_patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            line = m.group(0).strip()[:120]
            if line and line not in derogatory:
                derogatory.append(line)

    # Collections specifically
    collections = []
    for m in re.finditer(r'(?:COLLECTION\s*ACCOUNT|IN\s*COLLECTIONS?)[^\n]{0,120}', text, re.IGNORECASE):
        line = m.group(0).strip()[:120]
        if line not in collections:
            collections.append(line)

    # Public records (bankruptcies, judgments, liens)
    public_records = []
    for m in re.finditer(r'(?:BANKRUPTCY|JUDGMENT|TAX\s*LIEN|CIVIL\s*JUDGMENT)[^\n]{0,120}', text, re.IGNORECASE):
        line = m.group(0).strip()[:120]
        if line not in public_records:
            public_records.append(line)

    # Inquiries count
    inq_section = re.search(r'(?:Inquir(?:y|ies))[:\s]*([\s\S]{0,300})', text, re.IGNORECASE)
    inquiry_count = 0
    if inq_section:
        inq_nums = re.findall(r'\b(\d+)\s*inquir', inq_section.group(0), re.IGNORECASE)
        if inq_nums:
            inquiry_count = int(inq_nums[0])
        else:
            # Count individual inquiry lines
            inquiry_count = len(re.findall(r'\d{1,2}/\d{1,2}/\d{2,4}', inq_section.group(1)))

    # Total past due amount
    past_due_amounts = re.findall(r'Past\s*Due[:\s]+\$?([\d,]+)', text, re.IGNORECASE)
    total_past_due = sum(float(a.replace(',', '')) for a in past_due_amounts) if past_due_amounts else 0

    return {
        "borrower": {
            "name": name,
            "ssn": ssn,
            "dob": dob,
            "address": address,
            "employer": employer,
        },
        "scores": scores,
        "middle_score": middle_score,
        "middle_bureau": middle_bureau,
        "derogatory": derogatory[:10],
        "collections": collections[:10],
        "public_records": public_records[:5],
        "inquiry_count": inquiry_count,
        "total_past_due": total_past_due,
    }


# ---------------------------------------------------------------------------
# 1099 Parser
# ---------------------------------------------------------------------------

def extract_1099(text: str) -> dict:
    """
    Extract structured fields from a 1099 (NEC, MISC, INT, DIV, R, etc.).
    100% offline — regex only.
    """
    import re

    def _find(pattern, src, group=1, flags=re.IGNORECASE | re.MULTILINE):
        m = re.search(pattern, src, flags)
        if m:
            try:
                return m.group(group).strip()
            except Exception:
                return ""
        return ""

    def _money(val):
        if not val:
            return ""
        return re.sub(r'[^\d.]', '', val)

    # Form type
    form_type = _find(r'\b(1099[-\s]?(?:NEC|MISC|INT|DIV|R|G|K|S|C|B|OID|SA|LTC|Q|PATR)?)\b', text)
    if not form_type:
        form_type = "1099"

    # Tax year
    year = _find(r'(?:Tax\s*Year|for\s*(?:calendar\s*)?year)[:\s]+(\d{4})', text)
    if not year:
        year = _find(r'\b(20\d{2})\b', text)

    # Payer
    payer_name = _find(r"(?:Payer.{0,20}(?:name|s\s+name))[:\s]+([^\n]{3,60})", text)
    payer_tin  = _find(r"(?:Payer.{0,20}(?:TIN|EIN|ID))[:\s]+([\d\-]{9,12})", text)
    if not payer_tin:
        payer_tin = _find(r'\b(\d{2}-\d{7})\b', text)

    # Recipient
    recipient_name = _find(r"(?:Recipient.{0,20}(?:name|s\s+name))[:\s]+([^\n]{3,60})", text)
    recipient_ssn  = _find(r"(?:Recipient.{0,20}(?:TIN|SSN|ID))[:\s]*([\d\*X]{3}[-\s][\d\*X]{2}[-\s]\d{4})", text)
    if not recipient_ssn:
        recipient_ssn = _find(r'\b(\d{3}-\d{2}-\d{4}|XXX-XX-\d{4})\b', text)

    # Box amounts — key boxes by form type
    box1  = _find(r'(?:^|\b)(?:1\.?\s*(?:Non-?employee\s*[Cc]omp|Rents|Interest\s*Income|Gross\s*Distribution))[:\s]+([\d,\.]+)', text, flags=re.IGNORECASE|re.MULTILINE)
    box2  = _find(r'(?:2\.?\s*(?:Federal\s*Income\s*Tax\s*[Ww]ithheld|Royalties|Early\s*Distribution))[:\s]+([\d,\.]+)', text, flags=re.IGNORECASE|re.MULTILINE)
    box3  = _find(r'(?:3\.?\s*(?:Other\s*Income|Nontaxable\s*Distribution))[:\s]+([\d,\.]+)', text, flags=re.IGNORECASE|re.MULTILINE)
    box4  = _find(r'(?:4\.?\s*Federal\s*Income\s*Tax\s*[Ww]ithheld)[:\s]+([\d,\.]+)', text, flags=re.IGNORECASE|re.MULTILINE)

    # Fallback: positional — same pattern as W-2, grab first money cluster
    if not box1:
        money_lines = re.findall(r'^([\d,]+\.\d{2})(?:\s+([\d,]+\.\d{2}))?$', text, re.MULTILINE)
        money_lines = [(a, b) for a, b in money_lines if float(re.sub(r'[^\d.]', '', a) or '0') >= 1]
        if money_lines:
            box1 = money_lines[0][0]
            box2 = money_lines[0][1] if money_lines[0][1] else ""

    # Income calc
    income_val = float(_money(box1) or '0') if box1 else 0.0
    monthly = income_val / 12 if income_val else 0.0

    return {
        "form_type": form_type,
        "year": year,
        "payer_name": payer_name,
        "payer_tin": payer_tin,
        "recipient_name": recipient_name,
        "recipient_ssn": recipient_ssn,
        "box1": box1,
        "box2": box2,
        "box3": box3,
        "box4_fed_tax": box4,
        "annual_income": income_val,
        "monthly_income": monthly,
    }


# ---------------------------------------------------------------------------
# Mortgage Statement Parser
# ---------------------------------------------------------------------------

def extract_mortgage_statement(text: str) -> dict:
    import re

    def _find(pat, src, group=1, flags=re.IGNORECASE | re.MULTILINE):
        m = re.search(pat, src, flags)
        return m.group(group).strip() if m else ""

    def _find_after_label(label_pat, src, max_chars=80):
        """Find value that appears on the SAME line OR the NEXT line after a label."""
        m = re.search(label_pat + r'[:\s]*([^\n]{3,' + str(max_chars) + r'})', src, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            # If the same-line value looks like a real value (not just another label phrase), use it
            if val and not re.match(r'(?:is|are|the|of|for|your|our|this|a |an )', val, re.IGNORECASE):
                return val
        # Try next-line: label on one line, value on next
        m = re.search(label_pat + r'[:\s]*\n([^\n]{3,' + str(max_chars) + r'})', src, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return ""

    # Servicer: typically appears as company name near top or labeled
    # Try "serviced by CompanyName" or standalone labeled line
    servicer = _find(r'(?:serviced\s*by|mortgage\s*servicer|your\s*servicer\s*is)[:\s]+([A-Z][^\n]{3,50})', text)
    if not servicer:
        # Company name before "is responsible for" or "is the servicer"
        servicer = _find(r'([A-Z][A-Za-z\s,\.]+(?:Bank|Mortgage|Servicing|Financial|Home\s*Loans?|Federal|Corp|LLC|Inc))[^\n]{0,30}(?:servicer|responsible|collecting)', text)
    if not servicer:
        # First all-caps company name in first 500 chars
        m = re.search(r'([A-Z][A-Z\s&,\.]{5,50}(?:BANK|MORTGAGE|SERVICING|FINANCIAL|HOME|FEDERAL|CORP|LLC))', text[:600])
        if m:
            servicer = m.group(1).strip()

    # Borrower: "Borrower: Name" or "Account Holder: Name" or name labeled line
    borrower = _find(r'(?:^|\n)(?:borrower|account\s*holder|customer\s*name)[:\s]+([A-Z][A-Za-z\s\-\']{3,40})', text)
    if not borrower:
        # Name after "Dear" greeting
        borrower = _find(r'Dear\s+([A-Z][A-Za-z\s\-\']{3,40}),', text)
    if not borrower:
        # "Prepared for: Name" pattern
        borrower = _find(r'(?:prepared\s*for|statement\s*for)[:\s]+([A-Z][A-Za-z\s\-\']{3,40})', text)

    loan_num      = _find(r'(?:loan\s*(?:number|no\.?|#)|account\s*(?:number|no\.?|#))[:\s#]*([\d\-]{4,20})', text)
    prop_addr     = _find(r'(?:property\s*(?:address|location)|subject\s*property|property)[:\s]+(\d+[^\n]{5,70})', text)
    principal_bal = _find(r'(?:principal\s*balance|outstanding\s*(?:principal\s*)?balance|unpaid\s*(?:principal\s*)?balance)[:\s\$]*([\d,]+\.?\d*)', text)
    escrow_bal    = _find(r'(?:escrow\s*balance|escrow\s*account\s*balance)[:\s\$]*([\d,]+\.?\d*)', text)
    payment_amt   = _find(r'(?:(?:total\s*)?(?:amount\s*(?:due|enclosed)|monthly\s*payment(?:\s*amount)?|payment\s*amount|regular\s*payment))[:\s\$]*([\d,]+\.?\d*)', text)
    due_date      = _find(r'(?:payment\s*due\s*(?:date|by|on)|due\s*date|next\s*payment\s*due)[:\s]+([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4}|[A-Z][a-z]+\s+\d{1,2},?\s*\d{4}|\d{8})', text)
    interest_rate = _find(r'(?:interest\s*rate|note\s*rate|annual\s*(?:interest\s*)?rate)[:\s]+(\d+\.?\d*\s*%)', text)
    maturity      = _find(r'(?:maturity\s*date|loan\s*(?:matures|maturity)|maturity)[:\s]+([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4}|[A-Z][a-z]+\s+\d{1,2},?\s*\d{4}|\d{8})', text)
    ytd_interest  = _find(r'(?:year[\s\-]to[\s\-]date\s*interest(?:\s*paid)?|ytd\s*interest)[:\s\$]*([\d,]+\.?\d*)', text)

    return {
        "servicer": servicer,
        "borrower": borrower,
        "loan_number": loan_num,
        "property_address": prop_addr,
        "principal_balance": principal_bal,
        "escrow_balance": escrow_bal,
        "payment_amount": payment_amt,
        "due_date": due_date,
        "interest_rate": interest_rate,
        "maturity_date": maturity,
        "ytd_interest_paid": ytd_interest,
    }


# ---------------------------------------------------------------------------
# VA Certificate of Eligibility Parser
# ---------------------------------------------------------------------------

def extract_coe(text: str) -> dict:
    import re
    def _find(pat, src, group=1, flags=re.IGNORECASE | re.MULTILINE):
        m = re.search(pat, src, flags)
        return m.group(group).strip() if m else ""

    veteran_name  = _find(r'(?:veteran.{0,20}name|name\s*of\s*veteran|this\s*is\s*to\s*certify\s*that)[:\s]+([A-Z][^\n]{3,50})', text)
    if not veteran_name:
        veteran_name = _find(r'(?:borrower|applicant)[:\s]+([A-Z][a-zA-Z\-\'\s]{3,40})', text)
    service_num   = _find(r'(?:service\s*(?:number|no\.?)|va\s*file\s*(?:number|no\.?))[:\s#]*([\w\-]{5,15})', text)
    entitlement   = _find(r'(?:entitlement\s*(?:amount|code|charged))[:\s]+\$?([\d,\.]+)', text)
    ent_code      = _find(r'(?:entitlement\s*code)[:\s]+([^\n]{1,10})', text)
    funding_fee   = _find(r'(?:funding\s*fee)[:\s]+([^\n]{1,30})', text)
    exempt        = bool(re.search(r'(?:exempt(?:ion)?|waived|service[\s-]?connected\s*disability)', text, re.IGNORECASE))
    loan_guaranty = _find(r'(?:guaranty\s*(?:amount|percentage)|maximum\s*guaranty)[:\s]+\$?([\d,\.%]+)', text)
    coe_date      = _find(r'(?:date\s*(?:issued|of\s*issue|of\s*certificate))[:\s]+([^\n]{4,20})', text)
    remaining_ent = _find(r'(?:remaining\s*entitlement|available\s*entitlement)[:\s]+\$?([\d,\.]+)', text)

    return {
        "veteran_name": veteran_name,
        "service_number": service_num,
        "entitlement_amount": entitlement,
        "entitlement_code": ent_code,
        "remaining_entitlement": remaining_ent,
        "loan_guaranty": loan_guaranty,
        "funding_fee_exempt": exempt,
        "funding_fee_info": funding_fee,
        "issue_date": coe_date,
    }


# ---------------------------------------------------------------------------
# DD-214 Parser
# ---------------------------------------------------------------------------

def extract_dd214(text: str) -> dict:
    import re
    def _find(pat, src, group=1, flags=re.IGNORECASE | re.MULTILINE):
        m = re.search(pat, src, flags)
        return m.group(group).strip() if m else ""

    name          = _find(r'(?:1[a\.]?\s*name\s*(?:of\s*member)?|last\s*first\s*middle)[:\s]+([A-Z][^\n]{3,50})', text)
    if not name:
        name      = _find(r'^([A-Z]+,\s*[A-Z]+(?:\s+[A-Z]+)?)\s*$', text, flags=re.MULTILINE)
    ssn           = _find(r'(?:2[a\.]?\s*(?:social\s*security|ssn))[:\s]*([\dX\*]{3}[-\s][\dX\*]{2}[-\s]\d{4})', text)
    if not ssn:
        ssn       = _find(r'\b(\d{3}-\d{2}-\d{4}|XXX-XX-\d{4})\b', text)
    dob           = _find(r'(?:3[a\.]?\s*date\s*of\s*birth|dob)[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})', text)
    branch        = _find(r'(?:branch\s*of\s*service|component|armed\s*forces)[:\s]+([^\n]{3,40})', text)
    rank          = _find(r'(?:grade[,\s]*rate[,\s]*or\s*rank|rank\s*at\s*discharge)[:\s]+([^\n]{2,20})', text)
    entry_date    = _find(r'(?:date\s*entered\s*(?:active\s*duty|service)|entry\s*date)[:\s]+([^\n]{4,20})', text)
    separation    = _find(r'(?:date\s*of\s*(?:separation|discharge|release)|separation\s*date)[:\s]+([^\n]{4,20})', text)
    char_discharge= _find(r'(?:character\s*of\s*(?:service|discharge))[:\s]+([^\n]{3,40})', text)
    years_service = _find(r'(?:total\s*(?:active\s*)?(?:service|time))[:\s]+([^\n]{3,30})', text)
    disability    = bool(re.search(r'(?:service[\s-]?connected\s*disability|disabled\s*veteran|va\s*disability)', text, re.IGNORECASE))

    return {
        "name": name,
        "ssn": ssn,
        "dob": dob,
        "branch": branch,
        "rank": rank,
        "entry_date": entry_date,
        "separation_date": separation,
        "character_of_discharge": char_discharge,
        "total_service": years_service,
        "disability_noted": disability,
    }


# ---------------------------------------------------------------------------
# Government ID Parser
# ---------------------------------------------------------------------------

def extract_government_id(text: str) -> dict:
    import re
    def _find(pat, src, group=1, flags=re.IGNORECASE | re.MULTILINE):
        m = re.search(pat, src, flags)
        return m.group(group).strip() if m else ""

    # Determine ID type
    id_type = "Unknown ID"
    if re.search(r'driver.?s?\s*licen[sc]e', text, re.IGNORECASE):
        id_type = "Driver's License"
    elif re.search(r'social\s*security', text, re.IGNORECASE):
        id_type = "Social Security Card"
    elif re.search(r'passport', text, re.IGNORECASE):
        id_type = "Passport"
    elif re.search(r'state\s*id|identification\s*card', text, re.IGNORECASE):
        id_type = "State ID"
    elif re.search(r'military\s*id|common\s*access\s*card|cac\b', text, re.IGNORECASE):
        id_type = "Military ID"

    name    = _find(r'(?:name|full\s*name)[:\s]+([A-Z][a-zA-Z\-\'\s]{3,40})', text)
    if not name:
        name = _find(r'^([A-Z][A-Z\-\']+\s+[A-Z][A-Z\-\']+(?:\s+[A-Z][A-Z\-\']+)?)\s*$', text, flags=re.MULTILINE)

    dob     = _find(r'(?:dob|date\s*of\s*birth|birth\s*date)[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})', text)
    expiry  = _find(r'(?:exp(?:ires?|iration)?|expiry\s*date)[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})', text)
    issued  = _find(r'(?:issued|issue\s*date)[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})', text)
    id_num  = _find(r'(?:lic(?:ense)?\s*(?:no\.?|number|#)|id\s*(?:no\.?|number|#)|dl\s*(?:no\.?|number|#))[:\s#]*([\w\-]{4,20})', text)
    state   = _find(r'\b([A-Z]{2})\s+(?:driver|license|state\s*id)', text)
    address = _find(r'(?:address)[:\s]+(\d[^\n]{5,60})', text)
    ssn     = _find(r'\b(\d{3}-\d{2}-\d{4}|XXX-XX-\d{4})\b', text)

    return {
        "id_type": id_type,
        "name": name,
        "dob": dob,
        "expiry": expiry,
        "issued": issued,
        "id_number": id_num,
        "state": state,
        "address": address,
        "ssn": ssn,
    }


def extract_loan_estimate(text: str) -> dict:
    """Pull key fields from a Loan Estimate — most importantly lock_expiry.

    LE layout (TRID): top-right box has "Rate Lock" Yes/No and an expiry line
    "Until __/__/____ at __:__ a.m./p.m.". Also carries loan_amount, rate,
    loan_term, property address, borrower name — useful fallbacks.
    """
    import re

    def _find(pat, src=text, group=1, flags=re.IGNORECASE | re.DOTALL):
        m = re.search(pat, src, flags)
        return m.group(group).strip() if m else ""

    # Rate lock expiration — a few common phrasings
    lock_expiry = ""
    for pat in [
        # "...your rate is locked until MM/DD/YYYY at ..."
        r'rate\s*(?:is\s*)?lock(?:ed)?\s*(?:until|through|expires?)[^0-9]{0,40}'
        r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
        # "Lock Expires: MM/DD/YYYY" / "Lock Expiration MM/DD/YYYY"
        r'lock\s*(?:expir(?:es|ation)|exp\.?)\s*(?:date)?[:\s]*'
        r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
        # "Until MM/DD/YYYY at ... Before closing..." (TRID box wording)
        r'until\s+(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(?:at\s*\d{1,2}:\d{2})?\s*'
        r'(?:a\.?m\.?|p\.?m\.?)?[^.]{0,80}(?:before\s*closing|rate\s*lock)',
        # plain "Rate Lock ... YES ... MM/DD/YYYY"
        r'rate\s*lock[\s\S]{0,120}?yes[\s\S]{0,80}?(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            lock_expiry = m.group(1).strip()
            break

    # Normalize to YYYY-MM-DD when possible (pipeline stores it that way)
    if lock_expiry:
        m = re.match(r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})', lock_expiry)
        if m:
            mo, dy, yr = m.group(1), m.group(2), m.group(3)
            if len(yr) == 2:
                yr = ("20" + yr) if int(yr) < 80 else ("19" + yr)
            lock_expiry = f"{yr}-{int(mo):02d}-{int(dy):02d}"

    # Rate-lock Yes/No flag
    rate_locked = bool(re.search(
        r'rate\s*lock[\s\S]{0,80}?\byes\b', text, re.IGNORECASE
    )) or bool(lock_expiry)

    # Other useful fields (best-effort — LE layouts vary)
    loan_amount = _find(r'loan\s*amount[^$\d]{0,20}\$?\s*([\d,]+(?:\.\d{2})?)')
    interest_rate = _find(r'interest\s*rate[^%\d]{0,20}([\d.]+)\s*%')
    loan_term = _find(r'loan\s*term[^0-9]{0,20}(\d{1,3})\s*(?:years?|yrs?)')
    property_address = _find(
        r'property[:\s]+([0-9][^\n]{5,100}?)(?:\n|$)',
        flags=re.IGNORECASE,
    )
    borrower = _find(
        r'(?:applicants?|borrowers?)[:\s]+([A-Z][a-zA-Z\-\'&\s,.]{3,80}?)(?:\n|$)',
        flags=re.IGNORECASE,
    )
    issue_date = _find(
        r'(?:date\s*issued|issue\s*date)[:\s]*'
        r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})'
    )
    purpose = _find(r'\bpurpose[:\s]+([A-Za-z][A-Za-z\s/\-]{2,30})')

    return {
        "lock_expiry": lock_expiry,
        "rate_locked": rate_locked,
        "loan_amount": loan_amount,
        "interest_rate": interest_rate,
        "loan_term": loan_term,
        "property_address": property_address,
        "borrower": borrower,
        "issue_date": issue_date,
        "purpose": purpose,
    }


# ---------------------------------------------------------------------------
# Cloud AI augmentation merge helper
# ---------------------------------------------------------------------------

def _merge_pc_data(regex_data: dict, ai_data: dict) -> dict:
    """
    Merge cloud AI extraction into regex extraction.
    AI fills empty fields only — never overwrites a regex hit.
    Walks nested dicts (buyer, seller, listing_agent, selling_agent, title, transaction).
    """
    if not isinstance(regex_data, dict):
        return ai_data if isinstance(ai_data, dict) else {}
    if not isinstance(ai_data, dict):
        return regex_data

    merged = dict(regex_data)
    for key, ai_val in ai_data.items():
        regex_val = merged.get(key)

        # Nested dict: recurse
        if isinstance(ai_val, dict) and isinstance(regex_val, dict):
            merged[key] = _merge_pc_data(regex_val, ai_val)
        # Nested dict but regex had nothing
        elif isinstance(ai_val, dict) and not regex_val:
            merged[key] = ai_val
        # Lists: prefer the longer / non-empty one
        elif isinstance(ai_val, list):
            if not regex_val:
                merged[key] = ai_val
        # Scalars: only fill if regex was empty
        else:
            if regex_val in (None, "", 0) and ai_val not in (None, "", 0):
                merged[key] = ai_val
    return merged


# ---------------------------------------------------------------------------
# Main Processing Function
# ---------------------------------------------------------------------------

_SENSITIVE_BLOCK_TYPES = {
    "Bank Statement",
    "1003 Application",
}
_SENSITIVE_KEYWORDS = [
    r'\bssn\b', r'social\s+security\s+number', r'\d{3}[-\s]\d{2}[-\s]\d{4}',
    r'\bdob\b', r'date\s+of\s+birth',
    r'account\s+number', r'routing\s+number', r'routing\s+transit',
]
_SENSITIVE_RE = re.compile("|".join(_SENSITIVE_KEYWORDS), re.IGNORECASE)


def _has_sensitive_content(text: str) -> bool:
    return bool(_SENSITIVE_RE.search(text))


def process_document(pdf_bytes: bytes, doc_type: str, user_history=None, user_approved_cloud: bool = False) -> dict:
    """
    Main processing function. Takes PDF bytes, returns structured results.
    100% offline - no API calls. PDF is ONLY in memory.

    Args:
        pdf_bytes: PDF content as bytes
        doc_type: Document type string (e.g., "Purchase Contract")
        user_history: Optional user history for context
        user_approved_cloud: If True, allows cloud AI augmentation for cloud-enabled doc types
    """
    text = extract_text_from_pdf(pdf_bytes)

    # Image-based (scanned) PDFs — for certain doc types we can still succeed
    # with a stub result so the file is logged in the pipeline rather than erroring.
    _image_ok_types = {
        "VA Certificate of Eligibility", "DD-214", "Hazard Insurance",
        "Government ID", "Appraisal", "Purchase Contract",
    }
    if not text or len(text.strip()) < 50:
        if doc_type in _image_ok_types:
            return {
                "success": True,
                "doc_type": doc_type,
                "text_length": 0,
                "conditions": "",
                "risks": "",
                "bank_rules": "",
                "extracted_data": {"_image_only": True},
                "image_only": True,
            }
        return {
            "success": False,
            "error": "Could not extract enough text from this PDF. It may be a scanned image (OCR not yet supported in offline mode).",
            "conditions": "",
            "risks": "",
            "text_length": len(text) if text else 0,
        }

    result = {
        "success": True,
        "text_length": len(text),
        "doc_type": doc_type,
        "bank_rules": "",
    }

    if doc_type == "Bank Statement":
        result["conditions"] = ""
        result["bank_rules"] = check_bank_rules(text, user_history)
        result["bank_fields"] = extract_bank_statement_fields(text)
        result["bank_raw_text"] = text[:20000]  # kept for cross-reference
    elif doc_type == "1003 Application":
        result["conditions"] = ""
        result["extracted_data"] = extract_1003(text)
    elif doc_type == "W-2":
        result["conditions"] = ""
        result["extracted_data"] = extract_w2(text)
    elif doc_type == "1099":
        result["conditions"] = ""
        result["extracted_data"] = extract_1099(text)
    elif doc_type == "Credit Report":
        result["conditions"] = ""
        result["extracted_data"] = extract_credit_report(text)
    elif doc_type == "Mortgage Statement":
        result["conditions"] = ""
        result["extracted_data"] = extract_mortgage_statement(text)
    elif doc_type == "VA Certificate of Eligibility":
        result["conditions"] = ""
        result["extracted_data"] = extract_coe(text)
    elif doc_type == "DD-214":
        result["conditions"] = ""
        result["extracted_data"] = extract_dd214(text)
    elif doc_type == "Government ID":
        result["conditions"] = ""
        result["extracted_data"] = extract_government_id(text)
    elif doc_type == "Purchase Contract":
        result["conditions"] = ""
        regex_data = extract_purchase_contract(text)
        result["extracted_data"] = regex_data
        result["raw_text"] = text[:12000]  # retained for optional AI re-extraction

        # ── Cloud AI extraction ────────────────────────────────────────────
        # When the user explicitly approves cloud AI for this scan, AI WINS
        # over regex — because the user opted into AI specifically to get
        # better results than regex. Only fall back to a regex value if AI
        # returned an empty string for that field.
        if user_approved_cloud and _has_sensitive_content(text):
            result["ai_log"] = "Cloud AI blocked — document contains sensitive identifiers (SSN/DOB/Account/Routing)"
            user_approved_cloud = False
        if user_approved_cloud:
            try:
                import cloud_client as _cc
                if _cc.is_enabled():
                    ai_data, ai_log = _cc.extract_purchase_contract_ai(text)
                    # Store raw AI response for debugging
                    result["ai_raw"] = ai_data
                    if ai_data:
                        # AI takes priority — pass AI first so its values win
                        result["extracted_data"] = _merge_pc_data(ai_data, regex_data)
                        result["ai_log"] = ai_log
                    else:
                        result["ai_log"] = ai_log or "Cloud returned no data"
                else:
                    result["ai_log"] = "Cloud not enabled (sidebar toggle)"
            except Exception as _e:
                # Never let cloud failure block local extraction
                result["ai_log"] = f"Cloud augmentation FAILED: {type(_e).__name__}: {str(_e)[:120]}"
    elif doc_type == "Approval Letter":
        result["conditions"] = extract_conditions(text, doc_type, user_history)
        result["extracted_data"] = {}
        result["raw_text"] = text[:12000]  # retained for optional AI re-extraction

        # ── Cloud AI augmentation for Approval Letter ──────────────────
        if user_approved_cloud and _has_sensitive_content(text):
            result["ai_log"] = "Cloud AI blocked — document contains sensitive identifiers (SSN/DOB/Account/Routing)"
            user_approved_cloud = False
        if user_approved_cloud:
            try:
                import cloud_client as _cc
                if _cc.is_enabled():
                    enhanced_conditions, ai_log = _cc.enhance_conditions(
                        text, doc_type, result["conditions"]
                    )
                    if enhanced_conditions:
                        result["conditions"] = enhanced_conditions
                    result["ai_log"] = ai_log
            except Exception as _e:
                # Never let cloud failure block local extraction
                result["ai_log"] = f"Cloud augmentation skipped: {str(_e)[:80]}"
    elif doc_type in ("Loan Estimate (LE)", "Loan Estimate"):
        result["conditions"] = ""
        result["extracted_data"] = extract_loan_estimate(text)
    else:
        result["conditions"] = extract_conditions(text, doc_type, user_history)

    # ── Convert extracted data into contacts dictionary ──────────────────────
    # This allows the UI to suggest borrower names when starting a new loan
    extracted = result.get("extracted_data", {})
    contacts = {}
    
    if doc_type == "1003 Application" and isinstance(extracted, dict):
        # Add borrower
        if extracted.get("borrower_name"):
            contacts["borrower"] = {
                "name": extracted["borrower_name"],
                "phone": extracted.get("phone", ""),
                "email": extracted.get("email", ""),
                "dob": extracted.get("dob", ""),
            }
        # Add co-borrower
        if extracted.get("co_borrower_name"):
            contacts["co_borrower"] = {
                "name": extracted["co_borrower_name"],
                "phone": extracted.get("co_phone", ""),
                "email": extracted.get("co_email", ""),
            }
        # Add loan number if found
        if extracted.get("loan_num"):
            result["loan_num"] = extracted["loan_num"]
    
    elif doc_type == "Purchase Contract" and isinstance(extracted, dict):
        # Add buyer
        if extracted.get("buyer", {}).get("name"):
            contacts["buyer"] = extracted["buyer"]
        # Add seller
        if extracted.get("seller", {}).get("name"):
            contacts["seller"] = extracted["seller"]
        # Add agents
        if extracted.get("listing_agent", {}).get("name"):
            contacts["listing_agent"] = extracted["listing_agent"]
        if extracted.get("selling_agent", {}).get("name"):
            contacts["selling_agent"] = extracted["selling_agent"]
        # Add title company
        if extracted.get("title", {}).get("name"):
            contacts["title"] = extracted["title"]
    
    elif doc_type == "VA Certificate of Eligibility" and isinstance(extracted, dict):
        # Add veteran name
        if extracted.get("veteran_name"):
            contacts["veteran"] = {
                "name": extracted["veteran_name"],
                "service_num": extracted.get("service_num", ""),
            }
    
    elif doc_type == "Government ID" and isinstance(extracted, dict):
        # Add ID holder name
        if extracted.get("name"):
            contacts["id_holder"] = {
                "name": extracted["name"],
                "dob": extracted.get("dob", ""),
            }
    
    elif doc_type == "Mortgage Statement" and isinstance(extracted, dict):
        # Add borrower from mortgage statement
        if extracted.get("borrower"):
            contacts["borrower"] = {
                "name": extracted["borrower"],
            }
    
    elif doc_type == "Credit Report" and isinstance(extracted, dict):
        # Add consumer name from credit report
        if extracted.get("consumer_name"):
            contacts["consumer"] = {
                "name": extracted["consumer_name"],
            }
    
    if contacts:
        result["contacts"] = contacts

    return result

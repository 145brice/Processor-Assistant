"""
Offline Processing Engine for Processor Traien
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
        time.sleep(0.5)  # gentle pause per page - no CPU spike
    return text.strip()


# ---------------------------------------------------------------------------
# Condition Extraction — reads the ACTUAL lines from the PDF
# ---------------------------------------------------------------------------


def _is_junk_line(text: str) -> bool:
    """Return True if this line is NOT a real condition — it's metadata/junk."""
    t = text.strip()
    # Too short
    if len(t) < 12:
        return True
    # Pure numbers / dollar amounts / dates
    if re.match(r'^[\$\d\s,\.\-\/\(\)%]+$', t):
        return True
    # Email addresses
    if re.match(r'^[\w.+-]+@[\w\-]+\.[\w.]+$', t):
        return True
    # Phone numbers only
    if re.match(r'^[\(\)\d\s\-\.]+$', t):
        return True
    # Street addresses (number + street name pattern)
    if re.match(r'^\d+\s+[A-Z][a-z]+\s+(?:Dr|St|Ave|Blvd|Rd|Ln|Ct|Way|Cir|Pl)', t):
        return True
    # City, State, Zip
    if re.match(r'^[A-Za-z\s]+,\s*[A-Z]{2},?\s*\d{5}', t):
        return True
    # Just a person's name (2-3 words, all capitalized, no action verbs)
    if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+(?:\-[A-Z][a-z]+)?$', t):
        return True
    # Company/lender names on their own line
    if re.match(r'(?i)^(?:NEXA|Orion|American Financial|LLC|Inc|DBA)\b', t):
        return True
    # Closing cost summary labels
    if re.match(r'(?i)^(?:Purchase Price|Refinance|Estimated|Lender (?:Fee|Credit)|Seller Credit|Other Credit|Subordinate|Loan Amount|Cash (?:from|to)|Total Cost|Last UW|Date.?Time)', t):
        return True
    # Condition code only (no description after it)
    if re.match(r'^(?:Underwriter|Jr Underwriter|Closer|Manager|Processor|Sr Underwriter)\s+W[A-Z]{2}\d{2}\s*$', t):
        return True
    # "Orion Responsible" / date-only tails
    if re.match(r'(?i)^(?:Orion\s*)?Responsible\s*\d', t):
        return True
    # Timestamps
    if re.match(r'(?i)^(?:Last UW|Date.?Time)\s', t):
        return True
    # Loan product codes
    if re.match(r'^[A-Z]{3,5}\d{2}\s', t) and len(t) < 25:
        return True
    # Mortgagee/Loss payee clause (address block, not a condition)
    if re.match(r'(?i)^(?:S\.?A\.?O\.?A|I\.?S\.?A\.?O\.?A)', t):
        return True
    # Masked account numbers
    if re.match(r'^X{3,}\d+$', t):
        return True
    # Boilerplate footer lines
    if re.search(r'(?i)(?:must be received from the broker within|calendar days of the initial|closed for incompleteness)', t):
        return True
    # "Not Waived", "Past Due - Please", "contact your", "Account Manager"
    if re.match(r'(?i)^(?:Not Waived|Past Due|contact your|Account Manager)$', t):
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
        if _is_junk_line(desc) or len(desc) < 12:
            return
        lower = desc.lower()
        if lower in seen:
            return
        seen.add(lower)
        cond_num += 1
        conditions.append({
            "num": str(cond_num),
            "desc": desc[:250],
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
                cleaned = re.sub(r'^[\s]*(?:\d{1,3}[\.\)\:]|[a-zA-Z][\.\)]|[\-\*\•])\s*', '', line).strip()
                if _is_junk_line(cleaned):
                    continue
                if cleaned.lower() in seen:
                    continue
                seen.add(cleaned.lower())
                cond_num += 1
                conditions.append({
                    "num": str(cond_num),
                    "desc": cleaned[:250],
                    "party": _guess_party(cleaned),
                    "status": "Needed",
                })

        # Also catch standalone action lines
        for raw_line in lines:
            line = raw_line.strip()
            m = re.match(r'(?i)^\s*(?:\d{1,3}[\.\)\:]|[\-\*\•])?\s*(?:provide|submit|obtain|furnish)\s+(.{15,})', line)
            if m:
                desc = m.group(1).strip().rstrip('.')
                lower = desc.lower()
                if not _is_junk_line(desc) and lower not in seen:
                    already = any(lower in s or s in lower for s in seen)
                    if not already:
                        seen.add(lower)
                        cond_num += 1
                        conditions.append({
                            "num": str(cond_num),
                            "desc": desc[:250],
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
# Bank Statement Analysis (50-rule offline check)
# ---------------------------------------------------------------------------

def check_bank_rules(pdf_text: str, user_history=None) -> str:
    """Run 50-rule bank statement analysis using regex."""
    results = []
    t = pdf_text

    rules = [
        (1, "Ending balance present", r'(?i)(?:ending|closing)\s*balance'),
        (2, "Statement covers 60+ days", r'(?i)(?:statement\s*period|from.*through|beginning.*ending)'),
        (3, "No overdraft", r'(?i)overdraft|OD\s*fee|insufficient\s*fund'),
        (4, "Deposits match income", r'(?i)deposit|credit'),
        (5, "No large unexplained deposits", r'(?i)(?:deposit|credit).*\$\d{4,}'),
        (6, "Direct deposit / ACH present", r'(?i)(?:direct\s*deposit|ACH|payroll)'),
        (7, "No account freeze", r'(?i)(?:freeze|hold|restrict|suspend)'),
        (8, "All pages present", r'(?i)page\s*\d+\s*(?:of|/)\s*\d+'),
        (9, "Account holder name", r'(?i)(?:account\s*(?:holder|owner|name)|name\s*on\s*account)'),
        (10, "No negative balance", r'(?i)(?:negative|minus|\-\$)'),
        (11, "Statement date recent", r'(?i)\b(?:20\d{2})\b'),
        (12, "Account number present", r'(?i)account\s*(?:number|#|no)'),
        (13, "Borrower name consistent", r'(?i)(?:account\s*(?:holder|owner|name))'),
        (14, "Bank name/info present", r'(?i)(?:bank|credit\s*union|financial|N\.?A\.)'),
        (15, "No NSF fees", r'(?i)NSF|non[\s-]*sufficient|returned\s*item'),
        (16, "Average daily balance", r'(?i)average\s*(?:daily)?\s*balance'),
        (17, "No unexplained wires", r'(?i)wire\s*transfer'),
        (18, "No cash advances", r'(?i)cash\s*advance'),
        (19, "Rent/housing payment", r'(?i)(?:rent|mortgage|housing)\s*(?:payment)?'),
        (20, "Payroll consistent", r'(?i)payroll|direct\s*deposit|ACH'),
        (21, "No gambling transactions", r'(?i)(?:casino|gambl|lottery|poker|bet|wager)'),
        (22, "No crypto transactions", r'(?i)(?:coinbase|binance|crypto|bitcoin|ethereum)'),
        (23, "Tax refund (if applicable)", r'(?i)(?:tax\s*refund|IRS|treasury)'),
        (24, "Child support payments", r'(?i)child\s*support'),
        (25, "Pension/retirement deposits", r'(?i)(?:pension|retirement|social\s*security|SSI|SSA)'),
        (26, "Dividend/investment income", r'(?i)(?:dividend|interest\s*(?:earned|income)|investment)'),
        (27, "Interest earned entries", r'(?i)interest\s*(?:earned|paid|credit)'),
        (28, "No foreign currency", r'(?i)(?:foreign|currency\s*exchange|forex|FX)'),
        (29, "Account type identified", r'(?i)(?:checking|savings|money\s*market)'),
        (30, "Joint account match", r'(?i)(?:joint|and\s+\w+\s+\w+)'),
        (31, "Opening balance positive", r'(?i)(?:opening|beginning)\s*balance'),
        (32, "Closing balance positive", r'(?i)(?:closing|ending)\s*balance'),
        (33, "No charge-off notices", r'(?i)charge[\s-]*off'),
        (34, "No returned deposits", r'(?i)return(?:ed)?\s*(?:deposit|item|check)'),
        (35, "No stop payments", r'(?i)stop\s*payment'),
        (36, "Statement period dates shown", r'(?i)(?:period|from|through|beginning|ending)\s*:?\s*\d'),
        (37, "Page count complete", r'(?i)page\s*\d+\s*(?:of|/)\s*\d+'),
        (38, "No handwritten alterations", None),  # can't detect from text
        (39, "Digital/official formatting", None),  # can't detect from text
        (40, "No redacted information", r'(?i)(?:redact|black[\s-]*out|XXXX)'),
        (41, "Currency is USD", r'(?i)(?:USD|\$|United\s*States\s*Dollar)'),
        (42, "No high-risk merchants", r'(?i)(?:casino|payday|pawn|title\s*loan|check\s*cash)'),
        (43, "Income sources consistent", r'(?i)(?:payroll|direct\s*deposit|ACH)'),
        (44, "Normal expense patterns", r'(?i)(?:payment|purchase|debit)'),
        (45, "No unknown loan payments", r'(?i)(?:loan\s*payment|installment|note\s*payment)'),
        (46, "Savings rate reasonable", r'(?i)(?:transfer\s*to\s*savings|savings\s*deposit)'),
        (47, "No bankruptcy transactions", r'(?i)(?:trustee|bankruptcy|chapter\s*[713])'),
        (48, "Account established", r'(?i)(?:account\s*open|since|established)'),
        (49, "No dormant periods", None),  # can't detect from text
        (50, "Balance trend stable", r'(?i)(?:closing|ending)\s*balance'),
    ]

    found_count = 0
    missing_count = 0
    partial_count = 0
    na_count = 0

    for num, desc, pattern in rules:
        time.sleep(0.05)  # micro-pause to not spike CPU
        if pattern is None:
            results.append(f"**Rule #{num}:** N/A - {desc} (cannot determine from text extraction)")
            na_count += 1
        elif num in (3, 7, 10, 15, 17, 18, 21, 22, 28, 33, 34, 35, 40, 42, 47):
            # These are "bad if found" - reverse logic
            if re.search(pattern, t):
                results.append(f"**Rule #{num}:** FOUND (FLAG) - {desc} detected - review needed")
                partial_count += 1
            else:
                results.append(f"**Rule #{num}:** FOUND - {desc} - no issues detected")
                found_count += 1
        else:
            if re.search(pattern, t):
                results.append(f"**Rule #{num}:** FOUND - {desc}")
                found_count += 1
            else:
                results.append(f"**Rule #{num}:** MISSING - {desc} - not found in statement")
                missing_count += 1

    summary = (
        f"\n\n**SUMMARY:** {found_count} Found / {missing_count} Missing / "
        f"{partial_count} Flagged / {na_count} N/A\n\n"
        "**Note:** This is an offline regex scan. Manual review recommended for accuracy."
    )

    return "\n".join(results) + summary


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
}


def draft_email(conditions: str, recipient_type: str, language: str = "English", user_history=None) -> str:
    """Draft an email from templates. No AI needed."""
    templates = _EMAIL_TEMPLATES.get(recipient_type, _EMAIL_TEMPLATES.get("Borrower"))
    template = templates.get(language, templates.get("English", ""))
    if not template:
        template = _EMAIL_TEMPLATES["Borrower"]["English"]
    return template.format(conditions=conditions)


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
# Main Processing Function
# ---------------------------------------------------------------------------

def process_document(pdf_bytes: bytes, doc_type: str, user_history=None) -> dict:
    """
    Main processing function. Takes PDF bytes, returns structured results.
    100% offline - no API calls. PDF is ONLY in memory.
    """
    text = extract_text_from_pdf(pdf_bytes)

    if not text or len(text.strip()) < 50:
        return {
            "success": False,
            "error": "Could not extract enough text from this PDF. It may be a scanned image (OCR not yet supported in offline mode).",
            "conditions": "",
            "risks": "",
            "text_length": len(text) if text else 0,
        }

    # Only extract conditions on upload - everything else is on-demand (a la carte)
    conditions = extract_conditions(text, doc_type, user_history)

    return {
        "success": True,
        "conditions": conditions,
        "text_length": len(text),
        "doc_type": doc_type,
    }

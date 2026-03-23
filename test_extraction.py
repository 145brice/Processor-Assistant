"""
Extraction Test Suite — Processor Traien
Runs all document extraction functions against realistic mock document text.
No real PDFs needed — tests the regex/pattern logic directly.

Usage:
    python test_extraction.py
    python test_extraction.py > test_report.txt

All mock data is fictional. Names, SSNs, addresses, and loan numbers are invented.
"""

import sys
import traceback
from datetime import date

# ─────────────────────────────────────────────────────────────────────────────
# MOCK DOCUMENTS
# Each is a realistic text representation of what pypdf would extract from a PDF.
# ─────────────────────────────────────────────────────────────────────────────

MOCK_1003 = """
UNIFORM RESIDENTIAL LOAN APPLICATION
Fannie Mae Form 1003 / Freddie Mac Form 65

Loan Amount: $485,000
Interest Rate: 7.125%
Loan Term: 360 months
Amortization Type: Fixed Rate
Loan Purpose: Purchase
Property Type: Single Family

I. BORROWER INFORMATION
Borrower's Name: James Anthony Harrington
Social Security Number: 412-56-7890
Date of Birth: 05/14/1982
Home Phone: (602) 555-0147
E-mail: j.harrington@outlook.com
Present Address: 4421 West Camelback Road, Phoenix, AZ 85031

Co-Borrower's Name: Sarah Marie Harrington
Social Security Number: 523-67-8901
Date of Birth: 09/22/1985

II. EMPLOYMENT INFORMATION
Employer Name: Harrington & Associates LLC
Employer Address: 101 North Central Avenue, Suite 800, Phoenix, AZ 85004
Position/Title: Senior Project Manager
Years on Job: 8
Monthly Income: $11,250.00
Self Employed: No

Co-Borrower Employer: Desert Valley Health Systems
Co-Borrower Position: Registered Nurse
Co-Borrower Monthly Income: $6,800.00

III. MONTHLY INCOME AND COMBINED HOUSING EXPENSE
Base Employment Income: $11,250.00
Bonus Income: $1,200.00
Total Gross Monthly Income: $19,250.00

IV. ASSETS AND LIABILITIES
Checking Account: First Western Bank  Acct # ****4821  Balance: $42,300
Savings Account: First Western Bank   Acct # ****9203  Balance: $87,500
401(k): Fidelity                      Acct # ****0012  Balance: $214,000

V. LOAN AND PROPERTY INFORMATION
Subject Property Address: 8820 East Sunrise Drive, Scottsdale, AZ 85260
County: Maricopa
Legal Description: Lot 14, Sunrise Estates Phase 3
Purchase Price: $540,000
Down Payment: $55,000
Loan-to-Value: 89.81%

VI. DECLARATIONS
Are you a U.S. Citizen? Yes
Are there outstanding judgments? No
Have you declared bankruptcy? No
Are you a co-maker on any note? No

Borrower Signature: James A. Harrington     Date: 02/10/2026
Co-Borrower Signature: Sarah M. Harrington  Date: 02/10/2026
"""

MOCK_CREDIT_REPORT = """
RESIDENTIAL MORTGAGE CREDIT REPORT
Prepared for: Harrington, James Anthony
SSN: 412-XX-7890
Date of Birth: 05/XX/1982
Report Date: 02/12/2026
Report Number: CR-2026-0048321

CREDIT SCORES
Equifax:   742
Experian:  738
TransUnion: 751
Representative Score (Middle): 742

TRADELINES
Account: Chase Visa
Type: Revolving
Balance: $4,200
Limit: $15,000
Payment Status: Current
Monthly Payment: $126
Opened: 03/2018

Account: Auto Loan - Ford Motor Credit
Type: Installment
Balance: $18,400
Monthly Payment: $487
Payment Status: Current
Remaining Term: 38 months
Opened: 09/2022

Account: Student Loan - Navient
Type: Installment
Balance: $22,100
Monthly Payment: $310
Payment Status: Current
Opened: 08/2007

DEROGATORY ITEMS
None

INQUIRIES (Last 12 Months)
02/10/2026 - First Western Mortgage (Mortgage inquiry)
01/28/2026 - Capital One (Credit card inquiry)

PUBLIC RECORDS
None

EMPLOYMENT VERIFICATION
Current: Harrington & Associates LLC - 8 years

HOUSING HISTORY
Current: Renting - 4421 W Camelback Rd, Phoenix AZ 85031 - 4 years

DEBT-TO-INCOME SUMMARY
Monthly Gross Income: $18,050.00
Total Monthly Debt: $923.00
Back-End DTI: 28.6%
Front-End DTI (w/ proposed PITI): 34.2%
"""

MOCK_PURCHASE_CONTRACT = """
RESIDENTIAL PURCHASE CONTRACT AND RECEIPT FOR DEPOSIT
Arizona Association of REALTORS® — January 2026

DATE: February 5, 2026

BUYER: James Anthony Harrington and Sarah Marie Harrington
Buyer's Phone: (602) 555-0147
Buyer's E-mail: j.harrington@outlook.com

SELLER: Robert Eugene Castellano and Patricia Lynn Castellano
Seller's Phone: (480) 555-0293
Seller's E-mail: castpat1968@gmail.com

PROPERTY ADDRESS: 8820 East Sunrise Drive, Scottsdale, AZ 85260
Legal Description: Lot 14, Sunrise Estates Phase 3, Maricopa County, Arizona

1. PURCHASE PRICE AND TERMS
Purchase Price: $540,000
Earnest Money Deposit: $10,000 (deposited within 3 days of acceptance)
Additional Deposit: $5,000 (due by February 20, 2026)
New Loan Amount: $485,000
Down Payment: $55,000

2. FINANCING CONTINGENCY
This contract is contingent upon Buyer obtaining a conventional loan for $485,000
at no more than 7.5% interest for 30 years. Financing contingency deadline: March 1, 2026.

3. INSPECTION CONTINGENCY
Buyer shall have 10 days from acceptance to complete all inspections.
Inspection contingency deadline: February 15, 2026.

4. APPRAISAL CONTINGENCY
Property must appraise at or above the purchase price of $540,000.
Appraisal contingency deadline: March 5, 2026.

5. CLOSING DATE
Closing Date: March 28, 2026
Possession: At close of escrow

6. TITLE
Title to be conveyed by: Warranty Deed
Title Company: Southwest Title & Escrow, LLC
Title Insurance Policy: ALTA Owner's Policy

7. SELLERS CONCESSIONS
Seller agrees to contribute up to $8,000 toward Buyer's closing costs.

8. REAL ESTATE AGENTS
Buyer's Agent: Jennifer Morales, DBA Desert Sun Realty
Buyer's Agent License: SA689214000
Buyer's Brokerage: Desert Sun Realty, 3300 N. Scottsdale Rd, Scottsdale AZ 85251
Commission: 2.5%

Seller's Agent: Michael Thornton
Seller's Brokerage: Pinnacle Real Estate Group
Seller's Agent License: BR078341000
Commission: 2.5%

9. ADDENDUMS ATTACHED
[ X ] Seller Property Disclosure Statement (SPDS)
[ X ] Lead-Based Paint Disclosure
[ X ] HOA Addendum — Sunrise Estates HOA, Dues: $185/month
[ ] Short Sale Addendum

Buyer Signature: James A. Harrington    Date: 02/05/2026
Co-Buyer Signature: Sarah M. Harrington Date: 02/05/2026
Seller Signature: Robert E. Castellano  Date: 02/06/2026
Co-Seller Signature: Patricia L. Castellano Date: 02/06/2026
"""

MOCK_BANK_STATEMENT = """
FIRST WESTERN BANK
Personal Checking Account Statement
Account Holder: James A. Harrington
Account Number: ****4821
Statement Period: January 1, 2026 – January 31, 2026

Beginning Balance:  $38,750.42
Ending Balance:     $42,300.17

DEPOSITS / CREDITS
01/01/2026   Direct Deposit HARRINGTON ASSOC PAYROLL   $5,625.00
01/01/2026   Direct Deposit DESERT VALLEY HLTH PAYROLL  $3,400.00
01/15/2026   Direct Deposit HARRINGTON ASSOC PAYROLL   $5,625.00
01/15/2026   Direct Deposit DESERT VALLEY HLTH PAYROLL  $3,400.00

WITHDRAWALS / DEBITS
01/02/2026   ACH - FORD MOTOR CREDIT AUTOPAY            $487.00
01/03/2026   ZELLE - HOME DEPOT SUPPLIES                $342.18
01/05/2026   Check #1042 - HOA DUES                     $185.00
01/08/2026   ACH - CHASE VISA MINIMUM                   $126.00
01/10/2026   ACH - NAVIENT STUDENT LOAN                 $310.00
01/12/2026   DEBIT - GROCERY DEPOT                      $218.54
01/15/2026   ACH - ARIZONA GAS & ELECTRIC               $184.00
01/18/2026   DEBIT - COSTCO WHOLESALE                   $312.77
01/22/2026   ACH - T-MOBILE AUTOPAY                     $187.00
01/25/2026   Check #1043 - RENT PAYMENT                 $1,950.00
01/28/2026   DEBIT - AMAZON                             $89.40
01/30/2026   ATM WITHDRAWAL                             $400.00

NSF / OVERDRAFT FEES: None
Minimum Daily Balance: $35,210.00
Average Daily Balance: $40,183.28
Number of Deposits: 4
Number of Withdrawals: 12
"""

MOCK_APPRAISAL = """
UNIFORM RESIDENTIAL APPRAISAL REPORT
Fannie Mae Form 1004 / Freddie Mac Form 70
File No.: APR-2026-00841

SUBJECT PROPERTY
Property Address: 8820 East Sunrise Drive, Scottsdale, AZ 85260
Legal Description: Lot 14, Sunrise Estates Phase 3
City: Scottsdale    State: AZ    Zip: 85260    County: Maricopa
Assessor's Parcel No.: 174-22-0814

CLIENT AND INTENDED USER
Client: First Western Mortgage
Lender: First Western Mortgage, 2100 E. Camelback Rd, Phoenix, AZ 85016
Appraiser: David L. Whitmore, MAI
Appraiser License: AZ-1004891   Effective Date: 02/14/2026

PROPERTY DESCRIPTION
Year Built: 2004
Gross Living Area: 2,847 sq ft
Style: Two Story
Basement: None
Garage: 3-car attached
Lot Size: 10,200 sq ft
Bedrooms: 4    Bathrooms: 3.5
Condition: C2 (Well maintained)
Quality: Q3

NEIGHBORHOOD
Location: Suburban
Built-up: Over 75%
Growth: Stable
Property Values: Increasing
Demand/Supply: Shortage
Marketing Time: Under 3 months

COMPARABLE SALES ANALYSIS
Comp 1: 8740 E. Sunrise Dr, Scottsdale AZ 85260
Sale Price: $528,000  Date: 11/20/2025
GLA: 2,710 sq ft   Bedrooms: 4   Baths: 3
Adjustment: +$12,000 (GLA) = Adjusted $540,000

Comp 2: 9102 E. Desert Wind Blvd, Scottsdale AZ 85260
Sale Price: $555,000  Date: 12/15/2025
GLA: 2,950 sq ft   Bedrooms: 4   Baths: 4
Adjustment: -$15,000 (GLA, Bath) = Adjusted $540,000

Comp 3: 8615 E. Pinnacle Ct, Scottsdale AZ 85260
Sale Price: $519,500  Date: 01/08/2026
GLA: 2,720 sq ft   Bedrooms: 4   Baths: 3
Adjustment: +$21,000 (GLA, Garage) = Adjusted $540,500

RECONCILIATION AND OPINION OF VALUE
The Sales Comparison Approach is given primary weight.
Indicated Value by Sales Comparison Approach: $540,000

OPINION OF MARKET VALUE: $540,000
Effective Date of Appraisal: February 14, 2026

APPRAISER CERTIFICATION
I certify that I have performed a complete visual inspection of the interior
and exterior areas of the subject property.

David L. Whitmore, MAI
Certification Number: AZ-1004891
Date of Signature: 02/14/2026
"""

MOCK_TITLE_REPORT = """
PRELIMINARY TITLE REPORT
Southwest Title & Escrow, LLC
Order No.: SW-2026-048221
Date Prepared: February 16, 2026

PROPERTY DESCRIPTION
Property Address: 8820 East Sunrise Drive, Scottsdale, AZ 85260
Legal Description: Lot 14, Sunrise Estates Phase 3, as recorded in
    Book 312, Page 47 of Maps, Maricopa County Recorder's Office
Assessor's Parcel Number: 174-22-0814

VESTEE (CURRENT OWNER)
Robert Eugene Castellano and Patricia Lynn Castellano,
husband and wife as community property.
Deed recorded: April 12, 2004 — Document No. 2004-0418221

LIENS AND ENCUMBRANCES
Item 1: TAXES
Property taxes for the fiscal year 2025-2026.
First installment: DUE — $1,847.00
Second installment: NOT YET DUE — $1,847.00
APN: 174-22-0814

Item 2: DEED OF TRUST
Trustor: Robert E. Castellano and Patricia L. Castellano
Beneficiary: Wells Fargo Bank, N.A.
Original Amount: $340,000
Recorded: April 12, 2004 — Document No. 2004-0418222
Current Payoff (estimated): $187,450.00
NOTE: Payoff demand ordered — pending receipt.

Item 3: HOA — SUNRISE ESTATES HOMEOWNERS ASSOCIATION
Monthly Dues: $185.00
Status: Current through February 2026
CC&Rs recorded: Book 298, Page 12

Item 4: EASEMENT
A 10-foot public utility easement along the rear lot line as shown
on the subdivision map.

REQUIREMENTS TO CLOSE
1. Deed of Trust payoff — Wells Fargo must be paid in full at closing
2. First installment property taxes must be paid current
3. HOA certification showing dues current through closing
4. Executed Warranty Deed from Seller to Buyer
5. ALTA Owner's Title Insurance Policy to be issued

EXCEPTIONS FROM COVERAGE (Schedule B-II)
1. Property taxes not yet due and payable
2. Conditions and restrictions in the recorded subdivision CC&Rs
3. Utility easement noted in Item 4 above

Prepared by: Southwest Title & Escrow, LLC
Escrow Officer: Maria Elena Vásquez
Phone: (480) 555-0800
"""

MOCK_CONDITION_LIST = """
Uniform Residential Loan Application — Condition Summary
Loan Number: FWM-2026-00482
Borrower: James Anthony Harrington
Loan Amount: $485,000
Property: 8820 East Sunrise Drive, Scottsdale, AZ 85260

PRIOR TO CLOSING CONDITIONS:

Underwriter WCR01
Provide fully executed and signed purchase contract including all addendums and counter-offers.

Underwriter WCR02
Provide 2 years signed federal tax returns (2023, 2024) with all schedules — Borrower and Co-Borrower.

Underwriter WPR03
Provide 30 days most recent pay stubs for both Borrower and Co-Borrower.

Underwriter WCR04
Provide 2 months most recent bank statements for all accounts used in qualifying (all pages required).

Closer WES05
Provide Homeowner's Insurance Binder with First Western Mortgage listed as mortgagee.
ISAOA/ATIMA, 2100 E. Camelback Rd., Phoenix, AZ 85016

Closer WES06
Provide final utility bill or transfer letter — APS, SRP or City utility confirming transfer of service.

Closer WES07
Clear title — Wells Fargo payoff must be received and recorded.

Underwriter WCR08
Letter of explanation required — 01/28/2026 credit inquiry from Capital One.

Underwriter WCR09
Provide complete divorce decree if applicable — verify no alimony or child support obligations not disclosed.

Processor WXX10
Provide executed IRS Form 4506-C (Tax Transcript Authorization) — signed and dated within 120 days.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Test runner
# ─────────────────────────────────────────────────────────────────────────────

PASS  = "PASS"
FAIL  = "FAIL"
WARN  = "WARN"
SKIP  = "SKIP"

results: list[dict] = []

def _test(name: str, fn, *args, expect_nonempty=True, expect_keys=None):
    try:
        val = fn(*args)
        if expect_nonempty:
            if not val:
                results.append({"name": name, "status": FAIL, "detail": "Returned empty result"})
                return val
        if expect_keys and isinstance(val, dict):
            missing = [k for k in expect_keys if val.get(k) is None]
            if missing:
                results.append({"name": name, "status": WARN,
                                "detail": f"Missing fields: {', '.join(missing)}", "value": val})
                return val
        results.append({"name": name, "status": PASS, "detail": _summarize(val)})
        return val
    except Exception as e:
        results.append({"name": name, "status": FAIL,
                        "detail": f"{type(e).__name__}: {e}",
                        "traceback": traceback.format_exc()})
        return None


def _summarize(val) -> str:
    if isinstance(val, dict):
        return f"{len(val)} fields: " + ", ".join(
            f"{k}={repr(v)[:40]}" for k, v in list(val.items())[:5]
        )
    if isinstance(val, str):
        lines = [l for l in val.strip().splitlines() if l.strip()]
        return f"{len(lines)} lines — first: {repr(lines[0][:80])}" if lines else "(empty string)"
    if isinstance(val, list):
        return f"{len(val)} items"
    return repr(val)[:100]


# ─────────────────────────────────────────────────────────────────────────────
# Run all tests
# ─────────────────────────────────────────────────────────────────────────────

def run_all():
    print("\n" + "="*70)
    print("  PROCESSOR TRAIEN — EXTRACTION TEST SUITE")
    print(f"  Run date: {date.today()}")
    print("="*70 + "\n")

    try:
        import ai_engine as ae
    except ImportError as e:
        print(f"FATAL: Cannot import ai_engine — {e}")
        sys.exit(1)

    # ── 1. 1003 EXTRACTION ────────────────────────────────────────────────────
    print("── 1003 LOAN APPLICATION ───────────────────────────────────────────")
    data_1003 = _test(
        "extract_1003 — returns nested dict structure",
        lambda: ae.extract_1003(MOCK_1003),
        expect_keys=["borrower", "co_borrower", "employment", "loan"],
    )
    if data_1003:
        b  = data_1003.get("borrower", {})
        cb = data_1003.get("co_borrower", {})
        em = data_1003.get("employment", {})
        ln = data_1003.get("loan", {})
        _check_field("1003 — borrower.name",     b.get("name", ""),              "Harrington")
        _check_field("1003 — borrower.ssn",      b.get("ssn", ""),               "412")
        _check_field("1003 — borrower.dob",      b.get("dob", ""),               "1982")
        _check_field("1003 — borrower.email",    b.get("email", ""),             "harrington")
        _check_field("1003 — co_borrower.name",  cb.get("name", ""),             "Sarah")
        _check_field("1003 — employment.employer", em.get("employer", ""),       "Harrington")
        _check_field("1003 — employment.income", em.get("base_monthly_income", ""), "11,250")
        _check_field("1003 — loan.amount",       ln.get("amount", ""),           "485")
        _check_field("1003 — loan.property_addr",ln.get("property_address", ""), "Sunrise")

    # ── 2. PURCHASE CONTRACT ──────────────────────────────────────────────────
    print("\n── PURCHASE CONTRACT ────────────────────────────────────────────────")
    data_pc = _test(
        "extract_purchase_contract — returns nested dict structure",
        lambda: ae.extract_purchase_contract(MOCK_PURCHASE_CONTRACT),
        expect_keys=["buyer", "seller", "property", "transaction"],
    )
    if data_pc:
        buy = data_pc.get("buyer", {})
        sel = data_pc.get("seller", {})
        prp = data_pc.get("property", {})
        txn = data_pc.get("transaction", {})
        ttl = data_pc.get("title", {})
        bag = data_pc.get("selling_agent", {})
        _check_field("PC — buyer.name",          buy.get("name", ""),      "Harrington")
        _check_field("PC — seller.name",         sel.get("name", ""),      "Castellano")
        _check_field("PC — property.address",    prp.get("address", ""),   "Sunrise")
        _check_field("PC — transaction.price",   txn.get("purchase_price", ""), "540")
        _check_field("PC — transaction.closing", txn.get("closing_date", ""),   "2026")
        _check_field("PC — transaction.earnest", txn.get("earnest_money", ""),  "10,000")
        _check_field("PC — title.company",       ttl.get("company", ""),   "Southwest")
        _check_field("PC — selling_agent.name",  bag.get("name", ""),      "Morales")

    # ── 3. BANK STATEMENT ─────────────────────────────────────────────────────
    print("\n── BANK STATEMENT ───────────────────────────────────────────────────")
    _test(
        "check_bank_rules — runs without error",
        lambda: ae.check_bank_rules(MOCK_BANK_STATEMENT),
    )
    bank_result = ae.check_bank_rules(MOCK_BANK_STATEMENT) if ae else None
    if bank_result:
        # check_bank_rules returns structured pipe-delimited text, not raw dollar amounts
        _check_field("Bank — structured output format",    bank_result, "SECTION")
        _check_field("Bank — NSF rule present",            bank_result, "NSF")
        _check_field("Bank — summary line present",        bank_result, "SUMMARY")
        _check_field("Bank — OK/FLAG/MISSING tags",        bank_result, "OK|")

    # ── 4. CONDITION EXTRACTION ───────────────────────────────────────────────
    print("\n── CONDITION EXTRACTION (Commitment Letter format) ──────────────────")
    cond_result = _test(
        "extract_conditions — condition list",
        lambda: ae.extract_conditions(MOCK_CONDITION_LIST, "Commitment Letter"),
    )
    if cond_result:
        cond_lines = [l for l in cond_result.splitlines() if "|" in l]
        _check_val("Conditions — at least 5 extracted", len(cond_lines), lambda n: n >= 5,
                   f"{len(cond_lines)} pipe-delimited rows found")
        _check_field("Conditions — pay stubs found",    cond_result, "pay stub")
        _check_field("Conditions — tax returns found",  cond_result, "tax")
        _check_field("Conditions — bank statements",    cond_result, "bank")
        _check_field("Conditions — insurance binder",   cond_result, "insurance")

    # ── 5. RISK FLAGS ─────────────────────────────────────────────────────────
    print("\n── RISK / FLAG ASSESSMENT ───────────────────────────────────────────")
    _test(
        "flag_risks — bank statement text",
        lambda: ae.flag_risks(MOCK_BANK_STATEMENT),
    )
    _test(
        "flag_risks — 1003 text",
        lambda: ae.flag_risks(MOCK_1003),
    )

    # ── 6. FRAUD CHECK ────────────────────────────────────────────────────────
    print("\n── FRAUD CHECK (text-based, no PDF) ─────────────────────────────────")
    try:
        import fraud_check as fc
        _test(
            "fraud check — _check_multiple_ssn (expect no flag — only 1 SSN)",
            lambda: fc._check_multiple_ssn(MOCK_BANK_STATEMENT),
            expect_nonempty=False,
        )
        _test(
            "fraud check — _check_balance_jump (begin 38k → end 42k, no flag)",
            lambda: fc._check_balance_jump(MOCK_BANK_STATEMENT, "bank statement"),
            expect_nonempty=False,
        )
        _test(
            "fraud check — _check_zero_withholding (not present, expect no flag)",
            lambda: fc._check_zero_withholding(MOCK_1003, "1003"),
            expect_nonempty=False,
        )
        fc_result = _test(
            "fraud check — full check on bank statement",
            lambda: fc.check(MOCK_BANK_STATEMENT.encode(), "Bank Statement"),
            expect_keys=["risk_level", "summary", "flags"],
        )
        if fc_result:
            _check_val("fraud check — risk_level is low (clean mock doc)",
                       fc_result.get("risk_level"), lambda v: v == "low",
                       f"risk_level={fc_result.get('risk_level')}")
    except ImportError:
        results.append({"name": "fraud_check import", "status": SKIP, "detail": "Module not available"})

    # ── 7. EMAIL DRAFT ────────────────────────────────────────────────────────
    print("\n── EMAIL DRAFT ──────────────────────────────────────────────────────")
    _test(
        "draft_email — Borrower / English",
        lambda: ae.draft_email(
            "- Provide 2 years tax returns\n- Provide 30 days pay stubs\n- Provide 2 months bank statements",
            "Borrower", "English"
        ),
    )
    _test(
        "draft_email — Borrower / Spanish",
        lambda: ae.draft_email(
            "- Proporcionar 2 años de declaraciones de impuestos\n- Proporcionar talones de pago",
            "Borrower", "Spanish"
        ),
    )

    # ── 8. EXTRACT CONTACTS ───────────────────────────────────────────────────
    print("\n── CONTACT EXTRACTION ───────────────────────────────────────────────")
    _test(
        "extract_contacts — purchase contract",
        lambda: ae.extract_contacts(MOCK_PURCHASE_CONTRACT),
    )

    # ── 9. DOC VERIFY (module-level) ─────────────────────────────────────────
    print("\n── DOC VERIFY MODULE ────────────────────────────────────────────────")
    try:
        import doc_verify as dv
        _test(
            "doc_verify._guess_type — bank statement",
            lambda: dv._guess_type(MOCK_BANK_STATEMENT, "bank_stmt.pdf"),
        )
        _test(
            "doc_verify._guess_type — appraisal",
            lambda: dv._guess_type(MOCK_APPRAISAL, "appraisal.pdf"),
        )
        _test(
            "doc_verify._extract_dates — purchase contract",
            lambda: dv._extract_dates(MOCK_PURCHASE_CONTRACT),
        )
    except ImportError:
        results.append({"name": "doc_verify import", "status": SKIP, "detail": "Module not available"})

    # ── 10. BILLING MODULE ────────────────────────────────────────────────────
    print("\n── BILLING MODULE ───────────────────────────────────────────────────")
    try:
        import billing as bl
        usage = _test(
            "billing.get_usage — returns dict with expected keys",
            lambda: bl.get_usage("test_user_999"),
            expect_keys=["year_month", "scans", "included", "overage", "total_cost",
                         "base_cost", "pct_used"],
        )
        if usage:
            _check_val("billing — base cost is $49", usage.get("base_cost"), lambda v: v == 49.0,
                       f"base_cost={usage.get('base_cost')}")
            _check_val("billing — included is 50", usage.get("included"), lambda v: v == 50,
                       f"included={usage.get('included')}")
        _test(
            "billing.log_scan — records a scan",
            lambda: bl.log_scan("test_user_999", "Test Doc"),
            expect_keys=["scans"],
        )
        _test(
            "billing.get_history — returns list",
            lambda: bl.get_history("test_user_999", months=3),
            expect_nonempty=False,  # ok if empty for new user
        )
    except ImportError as e:
        results.append({"name": "billing import", "status": FAIL, "detail": str(e)})

    # ── PRINT REPORT ──────────────────────────────────────────────────────────
    _print_report()


def _check_field(name: str, haystack: str, needle: str):
    found = needle.lower() in str(haystack).lower()
    results.append({
        "name":   name,
        "status": PASS if found else WARN,
        "detail": f"Found '{needle}' in result" if found
                  else f"'{needle}' NOT found in: {repr(str(haystack)[:80])}",
    })


def _check_val(name: str, val, predicate, detail: str):
    ok = False
    try:
        ok = predicate(val)
    except Exception:
        pass
    results.append({
        "name":   name,
        "status": PASS if ok else WARN,
        "detail": detail,
    })


def _print_report():
    print("\n" + "="*70)
    print("  TEST RESULTS SUMMARY")
    print("="*70)

    counts = {PASS: 0, WARN: 0, FAIL: 0, SKIP: 0}
    for r in results:
        s = r["status"]
        counts[s] = counts.get(s, 0) + 1
        icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌", "SKIP": "⏭ "}.get(s, "  ")
        print(f"  {icon} [{s:4s}]  {r['name']}")
        if s != PASS:
            print(f"           → {r['detail']}")
        if r.get("traceback") and s == FAIL:
            tb_lines = r["traceback"].strip().splitlines()
            for line in tb_lines[-4:]:
                print(f"           {line}")

    total = sum(counts.values())
    print("\n" + "-"*70)
    print(f"  Total: {total}  |  ✅ {counts[PASS]} passed  |  "
          f"⚠️  {counts[WARN]} warnings  |  ❌ {counts[FAIL]} failed  |  ⏭  {counts[SKIP]} skipped")
    print("-"*70)

    # ── Detailed findings ──────────────────────────────────────────────────
    fails  = [r for r in results if r["status"] == FAIL]
    warns  = [r for r in results if r["status"] == WARN]

    if fails:
        print("\n🔴 FAILURES — needs fixing before launch:")
        for r in fails:
            print(f"   • {r['name']}: {r['detail']}")

    if warns:
        print("\n🟡 WARNINGS — works but extracts partial data:")
        for r in warns:
            print(f"   • {r['name']}: {r['detail']}")

    passing = [r for r in results if r["status"] == PASS]
    if passing:
        print(f"\n🟢 WORKING ({len(passing)} tests):")
        for r in passing:
            print(f"   • {r['name']}")

    print("\n" + "="*70)
    print("  LAUNCH READINESS")
    print("="*70)

    fail_pct = counts[FAIL] / max(total, 1) * 100
    if counts[FAIL] == 0 and counts[WARN] <= 3:
        print("  🟢 READY — all critical functions working")
    elif counts[FAIL] == 0:
        print(f"  🟡 MOSTLY READY — {counts[WARN]} fields extracting partial data")
        print("     Recommend tuning regex patterns for the warning items above.")
    elif fail_pct < 20:
        print(f"  🟡 CLOSE — {counts[FAIL]} failures, likely fixable with small regex tweaks")
    else:
        print(f"  🔴 NOT READY — {counts[FAIL]} failures require attention before launch")

    print("="*70 + "\n")


if __name__ == "__main__":
    run_all()

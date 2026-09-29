"""Create a fictional conditional approval PDF for Processor Assistant demos.

Usage:
    python scripts/make_demo_approval.py
    python scripts/make_demo_approval.py --output generated_docs/my_demo.pdf --seed 2

The generator contains no customer records or lender documents.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import fitz


NAVY = (0.09, 0.16, 0.27)
BLUE = (0.13, 0.32, 0.53)
PALE = (0.93, 0.96, 0.98)
GRAY = (0.36, 0.42, 0.49)
GREEN = (0.10, 0.43, 0.35)
PAGE_W, PAGE_H = 612, 792

PEOPLE = [
    ("Alex Sample", "Taylor Sample", "1847 Demo Park Drive, Sampleville, IL 00000"),
    ("Jordan Example", "Casey Example", "2064 Fiction Lane, Sampleville, IL 00000"),
    ("Morgan Demo", "Riley Demo", "3178 Practice Court, Sampleville, IL 00000"),
]

CONDITIONS = [
    ("3365-4-4-51", "Income Documentation", "Provide the most recent 30 days of paystubs for each borrower."),
    ("3365-4-4-52", "Asset Documentation", "Provide two most recent monthly bank statements showing funds to close."),
    ("3365-4-4-53", "Earnest Money", "Provide evidence that the earnest money deposit cleared the borrower's account."),
    ("3365-4-4-54", "Homeowners Insurance", "Provide an insurance binder with coverage and mortgagee clause for the subject property."),
    ("3365-4-4-55", "Appraisal", "Provide the final appraisal supporting the contract price and property condition."),
    ("3365-4-4-56", "Title Commitment", "Provide a title commitment showing clear, marketable title and all liens addressed."),
    ("3365-4-4-57", "Employment Verification", "Complete verbal verification of employment within 10 business days of closing."),
    ("3365-4-4-58", "Gift Funds", "Provide a signed gift letter and evidence of donor funds, if gift funds are used."),
    ("3365-4-4-59", "Credit Inquiry", "Provide a signed letter of explanation for the recent credit inquiry."),
    ("3365-4-4-60", "Government ID", "Provide a clear copy of each borrower's unexpired government-issued ID."),
    ("3365-4-4-61", "Closing Disclosure", "Provide the final Closing Disclosure for lender review before signing."),
    ("3365-4-4-62", "Funding Review", "Confirm all prior-to-funding conditions are satisfied before disbursement."),
]


def _text(page: fitz.Page, x: float, y: float, value: str, *, size: float = 10,
          color: tuple[float, float, float] = NAVY, bold: bool = False) -> None:
    page.insert_text((x, y), value, fontsize=size, fontname="hebo" if bold else "helv", color=color)


def _page(doc: fitz.Document, page_number: int, issued: date) -> fitz.Page:
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    page.draw_rect(fitz.Rect(0, 0, PAGE_W, 11), color=BLUE, fill=BLUE)
    _text(page, 42, 43, "PINE HARBOR HOME LOANS", size=14, color=BLUE, bold=True)
    _text(page, 43, 61, "FICTIONAL LENDER  |  TRAINING DOCUMENT", size=8, color=GRAY)
    page.draw_line((42, 76), (570, 76), color=(0.79, 0.84, 0.88), width=1)
    page.draw_rect(fitz.Rect(42, 748, 570, 773), color=PALE, fill=PALE)
    _text(page, 52, 764, "DEMO ONLY - FICTIONAL PEOPLE, PROPERTY AND LOAN", size=8, color=BLUE, bold=True)
    _text(page, 530, 764, f"{page_number} / 2", size=8, color=GRAY)
    _text(page, 42, 739, "Not a credit decision, commitment, or document from a real lender.", size=8, color=GRAY)
    return page


def _condition(page: fitz.Page, y: float, code: str, title: str, description: str) -> None:
    _text(page, 44, y, f"{code}  {title}", size=9, bold=True)
    _text(page, 58, y + 16, description, size=8.5)
    page.draw_line((44, y + 28), (568, y + 28), color=(0.87, 0.90, 0.93), width=0.5)


def make_pdf(output: Path, seed: int = 1, issued: date | None = None) -> Path:
    if seed < 1:
        raise ValueError("seed must be a positive integer")
    issued = issued or date.today()
    borrower, co_borrower, property_address = PEOPLE[(seed - 1) % len(PEOPLE)]
    loan_number = f"DEMO-LOAN-{seed:05d}"
    amount = 325_000 + ((seed - 1) % 3) * 25_000

    doc = fitz.open()
    page = _page(doc, 1, issued)
    _text(page, 42, 106, "CONDITIONAL LOAN APPROVAL", size=18, bold=True)
    _text(page, 43, 126, "Underwriting decision: Approved subject to the conditions below", size=10, color=GREEN)

    page.draw_rect(fitz.Rect(42, 146, 570, 298), color=PALE, fill=PALE)
    fields = [
        ("Borrower", borrower, "Co-borrower", co_borrower),
        ("Loan number", loan_number, "Decision date", issued.strftime("%B %d, %Y")),
        ("Loan purpose", "Purchase", "Loan program", "30-year fixed conventional"),
        ("Loan amount", f"${amount:,.00f}", "Approval expires", (issued + timedelta(days=45)).strftime("%B %d, %Y")),
    ]
    for i, (left_label, left_value, right_label, right_value) in enumerate(fields):
        y = 165 + i * 31
        _text(page, 54, y, left_label.upper(), size=7, color=GRAY, bold=True)
        _text(page, 54, y + 14, left_value, size=9.5)
        _text(page, 317, y, right_label.upper(), size=7, color=GRAY, bold=True)
        _text(page, 317, y + 14, right_value, size=9.5)
    _text(page, 54, 289, "SUBJECT PROPERTY", size=7, color=GRAY, bold=True)
    _text(page, 170, 289, property_address, size=9)

    _text(page, 42, 331, "DECISION SUMMARY", size=13, color=BLUE, bold=True)
    _text(page, 42, 357, "This fictional loan is conditionally approved for demonstration purposes.", size=10)
    _text(page, 42, 377, "The itemized underwriting conditions are listed on the following page.", size=10)
    _text(page, 42, 427, "REVIEW MILESTONES", size=13, color=BLUE, bold=True)
    _text(page, 42, 454, "1. Collect borrower, property, and third-party documents.", size=10)
    _text(page, 42, 477, "2. Submit the condition package for lender review.", size=10)
    _text(page, 42, 500, "3. Confirm closing and funding conditions are cleared.", size=10)
    page.draw_rect(fitz.Rect(42, 552, 570, 624), color=PALE, fill=PALE)
    _text(page, 56, 577, "TRAINING COPY", size=11, color=BLUE, bold=True)
    _text(page, 56, 599, "All names, numbers, amounts, and property details were created for this demo.", size=9)

    page = _page(doc, 2, issued)
    _text(page, 42, 110, "LOAN APPROVAL CONDITIONS", size=15, color=BLUE, bold=True)
    _text(page, 42, 130, f"{borrower}  |  {loan_number}  |  Prior to documents / closing / funding", size=9, color=GRAY)
    y = 157
    for code, title, description in CONDITIONS:
        _condition(page, y, code, title, description)
        y += 45

    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output), garbage=4, deflate=True)
    doc.close()
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("generated_docs/demo_conditional_approval.pdf"))
    parser.add_argument("--seed", type=int, default=1, help="Positive integer for a repeatable fictional case")
    args = parser.parse_args()
    print(make_pdf(args.output, args.seed).resolve())


if __name__ == "__main__":
    main()

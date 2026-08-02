"""End-to-end demonstration of the sanitize -> LLM -> restore flow.

Run:
    python -m pii_sanitizer.example.demo
    python -m pii_sanitizer.example.demo path/to/document.pdf   # real PDF path

No network calls are made; ``fake_gemini`` stands in for the real LLM so you can
see exactly what the model would receive (only placeholders) and how the
originals are restored locally afterwards.
"""

from __future__ import annotations

import sys

from pii_sanitizer import SanitizerConfig, restore, sanitize_pdf, sanitize_text

SAMPLE_TEXT = """LENDER CONDITION LETTER

Borrower: John Smith
Co-Borrower: Jane Smith
Loan Officer: Alex Reed
Processor: Maria Gomez
Property: 123 Main Street, Springfield, IL 62704
Loan Number: ABC1234567
SSN: 123-45-6789
Date of Birth: 01/02/1980
Email: john.smith@example.com
Phone: (555) 123-4567
Employer: Acme Manufacturing LLC

Conditions:
1. Provide most recent bank statement for account ending 4567.
2. Verify borrower income of $8,500/month.
3. Confirm homeowners insurance for the subject property.
"""


def fake_gemini(sanitized_prompt: str) -> str:
    """Pretend LLM. Echoes placeholders back the way a real model would."""
    return (
        "SUMMARY: The primary applicant [BORROWER_1] and co-applicant "
        "[COBORROWER_1] have 3 outstanding conditions on loan [LOAN_NUMBER_1] "
        "for the property at [ADDRESS_1]. Processor [PROCESSOR_1] should follow "
        "up with [BORROWER_1] at [EMAIL_1] / [PHONE_1]. Condition 1 requires a "
        "bank statement; conditions 2-3 concern income and insurance."
    )


def _banner(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main() -> None:
    config = SanitizerConfig(strict_gate=True)

    if len(sys.argv) > 1:
        with open(sys.argv[1], "rb") as fh:
            result = sanitize_pdf(fh.read(), config=config)
        if result.extraction:
            print(
                f"[extraction] pages={result.extraction.page_count} "
                f"ocr_pages={result.extraction.ocr_page_numbers} "
                f"image_based={result.extraction.is_image_based}"
            )
    else:
        result = sanitize_text(SAMPLE_TEXT, config=config)

    _banner("1. ORIGINAL (stays local — never sent)")
    print(SAMPLE_TEXT if len(sys.argv) == 1 else "<from PDF>")

    _banner("2. SANITIZED TEXT SENT TO GEMINI (only this leaves the machine)")
    print(result.sanitized_text)
    print(f"\n[gate] residual leaks: {result.residual_leaks or 'none'}")
    print(f"[detect] entity counts: {result.entity_counts}")

    _banner("3. GEMINI RESPONSE (contains placeholders only)")
    llm_response = fake_gemini(result.sanitized_text)
    print(llm_response)

    _banner("4. RESTORED OUTPUT (originals put back locally, shown to user)")
    final = restore(llm_response, result.vault)
    print(final)

    # Always zeroize the mapping when finished with the document.
    result.vault.close()
    print("\n[vault] closed and zeroized.")


if __name__ == "__main__":
    main()

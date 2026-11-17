from pii_sanitizer.integration import (
    redact_for_cloud_resilient,
    require_cloud_safe,
    restore_local_placeholders,
    secure_approval_system_prompt,
)


def test_resilient_redaction_combines_typed_and_legacy_rules():
    text = (
        "Borrower: Jane Example\n"
        "Monthly income: $8,500\n"
        "Routing number: 021000021"
    )

    sanitized, replacements, forced, remaining = redact_for_cloud_resilient(text)

    assert "Jane Example" not in sanitized
    assert "$8,500" not in sanitized
    assert "021000021" not in sanitized
    assert any(key.startswith("[BORROWER_") for key in replacements)
    assert remaining == []
    require_cloud_safe(sanitized)


def test_restore_is_case_insensitive_for_model_echoes():
    assert restore_local_placeholders(
        "Contact [borrower_1]",
        {"[BORROWER_1]": "Jane Example"},
    ) == "Contact Jane Example"


def test_secure_prompt_remains_available_through_integration():
    prompt = secure_approval_system_prompt("Extract conditions.")
    assert "Extract conditions." in prompt
    assert "privacy" in prompt.lower() or "sensitive" in prompt.lower()


def test_names_on_line_below_label_are_redacted():
    text = "BORROWER\nAlex Sample\nCO-BORROWER\nTaylor Sample\nLOAN PURPOSE\nPurchase"

    sanitized, _, _, _ = redact_for_cloud_resilient(text)

    assert "Alex" not in sanitized and "Taylor" not in sanitized
    assert "Purchase" in sanitized


def test_ocr_side_by_side_party_columns_are_redacted():
    # OCR reads two label columns onto one line, then both names onto the next.
    text = "BORROWER CO-BORROWER\nAlex Sample Taylor Sample\nLOAN NUMBER"

    sanitized, _, _, _ = redact_for_cloud_resilient(text)

    assert "Alex" not in sanitized and "Taylor" not in sanitized


def test_known_values_redact_unlabeled_names():
    text = "Per our call, Robert Kim will upload the VOE today."

    sanitized, _, _, _ = redact_for_cloud_resilient(text, known_values=["Robert Kim"])

    assert "Robert Kim" not in sanitized


def test_role_prefixed_names_in_conditions_are_redacted():
    text = "3. Gift letter signed by donor Elena Vasquez\n4. Loan officer Jordan Whitfield to confirm lock"

    sanitized, _, _, _ = redact_for_cloud_resilient(text)

    assert "Elena" not in sanitized and "Whitfield" not in sanitized
    assert "Gift letter" in sanitized


def test_section_headers_are_not_mistaken_for_names():
    text = "Borrower Conditions\n1. Provide Final Seller Disclosure from sale of current home"

    sanitized, _, _, _ = redact_for_cloud_resilient(text)

    assert "Borrower Conditions" in sanitized
    assert "Final Seller Disclosure" in sanitized


def test_loan_number_in_column_layout_does_not_block_document():
    text = ("LOAN NUMBER PROPERTY\n7744120931 2218 Willow Bend Ct\n"
            "CONDITIONS\n1. Provide VOE")

    sanitized, _, _, remaining = redact_for_cloud_resilient(text)

    assert "7744120931" not in sanitized
    assert "Provide VOE" in sanitized and not remaining


def test_reply_scrubber_catches_company_without_suffix():
    from pii_sanitizer.integration import redact_gemini_output

    source = "Employer: Harbor Freight Logistics LLC"
    reply = "| 1 | VOE from Harbor Freight Logistics | Borrower | Needed | High |"

    assert "Harbor Freight" not in redact_gemini_output(reply, source_text=source)

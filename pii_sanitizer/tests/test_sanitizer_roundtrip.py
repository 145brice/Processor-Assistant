"""End-to-end: sanitize -> (fake LLM) -> restore, with the gate enforcing safety."""

from __future__ import annotations

import pytest

from pii_sanitizer import SanitizerConfig, restore, sanitize_text
from pii_sanitizer.errors import LeakDetectedError
from pii_sanitizer.gate import find_leaks

# NER may be unavailable in CI; force regex-only so the test is deterministic.
CFG = SanitizerConfig(enable_ner=False, enable_barcode=False)

SAMPLE = (
    "Borrower: John Smith\n"
    "Co-Borrower: Jane Smith\n"
    "Property: 123 Main Street, Springfield, IL 62704\n"
    "Loan Number: ABC1234567\n"
    "SSN: 123-45-6789\n"
    "Email: john.smith@example.com\n"
    "Phone: (555) 123-4567\n"
)


def test_no_structured_pii_survives_sanitization():
    result = sanitize_text(SAMPLE, config=CFG)
    assert result.residual_leaks == []
    assert find_leaks(result.sanitized_text) == []
    # Originals must be gone from the cloud-bound text.
    for secret in ["123-45-6789", "john.smith@example.com", "123 Main Street", "ABC1234567"]:
        assert secret not in result.sanitized_text


def test_placeholders_are_typed_and_deterministic():
    result = sanitize_text(SAMPLE, config=CFG)
    assert "[BORROWER_1]" in result.sanitized_text
    assert "[COBORROWER_1]" in result.sanitized_text
    assert "[SSN_1]" in result.sanitized_text


def test_restore_reproduces_originals():
    result = sanitize_text(SAMPLE, config=CFG)
    # Simulate an LLM answer that references the placeholders.
    llm = (
        "The primary applicant is [BORROWER_1] with co-applicant [COBORROWER_1]. "
        "Verify SSN [SSN_1] and email [EMAIL_1]."
    )
    final = restore(llm, result.vault)
    assert "John Smith" in final
    assert "Jane Smith" in final
    assert "123-45-6789" in final
    assert "john.smith@example.com" in final
    assert "[" not in final.replace("[LOCAL OCR TEXT]", "")  # no stray placeholders


def test_repeated_value_maps_to_one_placeholder():
    text = "John Smith signed. Later, John Smith initialed again. Borrower: John Smith"
    result = sanitize_text(text, config=CFG, known_values=["John Smith"])
    # Exactly one distinct placeholder for the repeated name.
    assert result.sanitized_text.count("[PERSON_1]") + result.sanitized_text.count("[BORROWER_1]") >= 2
    assert "John Smith" not in result.sanitized_text


def test_known_values_typed_override():
    text = "The buyer visited. The buyer is happy."
    result = sanitize_text(text, config=CFG, known_values={"buyer": "BUYER"})
    assert "[BUYER_1]" in result.sanitized_text


def test_strict_gate_raises_on_engineered_leak():
    # A value the detectors can't catch but the gate can (bare SSN with no label
    # is caught, so use a normal SSN and disable regex to force a miss).
    cfg = SanitizerConfig(enable_ner=False, enable_regex=False, strict_gate=True)
    with pytest.raises(LeakDetectedError):
        sanitize_text("SSN 123-45-6789", config=cfg)


def test_gate_message_never_contains_the_value():
    cfg = SanitizerConfig(enable_ner=False, enable_regex=False, strict_gate=True)
    try:
        sanitize_text("SSN 123-45-6789", config=cfg)
        assert False, "should have raised"
    except LeakDetectedError as exc:
        assert "123-45-6789" not in str(exc)
        assert "ssn" in str(exc)

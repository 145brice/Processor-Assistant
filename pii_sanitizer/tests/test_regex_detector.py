"""Regex detector: structured identifiers and role-typed labeled names."""

from __future__ import annotations

from pii_sanitizer.detectors import regex_detector


def _types(text):
    return {s.entity_type for s in regex_detector.detect(text)}


def _find(text, entity):
    return [s for s in regex_detector.detect(text) if s.entity_type == entity]


def test_ssn():
    assert _find("SSN 123-45-6789 on file", "SSN")


def test_email_and_phone():
    t = "Reach me at jane.doe@example.com or (555) 123-4567."
    types = _types(t)
    assert "EMAIL" in types and "PHONE" in types


def test_labeled_roles_get_typed():
    t = "Borrower: John Smith\nCo-Borrower: Jane Smith\nProcessor: Alex Reed"
    borrowers = _find(t, "BORROWER")
    coborrowers = _find(t, "COBORROWER")
    processors = _find(t, "PROCESSOR")
    assert borrowers and borrowers[0].text.strip() == "John Smith"
    assert coborrowers and coborrowers[0].text.strip() == "Jane Smith"
    assert processors and processors[0].text.strip() == "Alex Reed"


def test_loan_number():
    hits = _find("Loan Number: ABC1234567", "LOAN_NUMBER")
    assert hits and "ABC1234567" in hits[0].text


def test_routing_and_account():
    t = "Routing Number: 021000021 Account No: 000123456789"
    types = _types(t)
    assert "ROUTING_NUMBER" in types
    assert "ACCOUNT_NUMBER" in types


def test_address():
    assert _find("Property: 123 Main Street, Springfield, IL 62704", "ADDRESS")


def test_dob():
    assert _find("DOB: 01/02/1980", "DATE_OF_BIRTH")


def test_company_suffix():
    assert _find("Loan from Wells Fargo Bank and Acme Mortgage LLC", "COMPANY")


def test_disabled_entities_are_skipped():
    from pii_sanitizer.config import SanitizerConfig

    cfg = SanitizerConfig(enabled_entities=("EMAIL",))
    spans = regex_detector.detect("SSN 123-45-6789 email a@b.com", cfg)
    types = {s.entity_type for s in spans}
    assert types == {"EMAIL"}

"""Cloud gate leak detection and the redaction-safe logging filter."""

from __future__ import annotations

import logging

import pytest

from pii_sanitizer.gate import find_leaks, is_cloud_safe, require_cloud_safe
from pii_sanitizer.errors import LeakDetectedError
from pii_sanitizer.logging_utils import RedactingFilter, configure_logging, scrub


def test_gate_ignores_placeholders():
    assert find_leaks("Contact [EMAIL_1] about [SSN_1]") == []
    assert is_cloud_safe("Contact [EMAIL_1] about [SSN_1]")


def test_gate_flags_each_category():
    assert "ssn" in find_leaks("123-45-6789")
    assert "email" in find_leaks("a@b.com")
    assert "phone" in find_leaks("(555) 123-4567")


def test_require_cloud_safe_raises():
    with pytest.raises(LeakDetectedError):
        require_cloud_safe("SSN 123-45-6789")


def test_scrub_masks_pii():
    out = scrub("SSN 123-45-6789 email a@b.com phone 555-123-4567 acct 12345678")
    assert "123-45-6789" not in out
    assert "a@b.com" not in out
    assert "[SSN]" in out and "[EMAIL]" in out


def test_redacting_filter_scrubs_log_message(caplog):
    logger = logging.getLogger("pii_sanitizer.test")
    logger.addFilter(RedactingFilter())
    logger.setLevel(logging.INFO)
    with caplog.at_level(logging.INFO, logger="pii_sanitizer.test"):
        logger.info("borrower ssn is 123-45-6789")
    assert "123-45-6789" not in caplog.text
    assert "[SSN]" in caplog.text


def test_configure_logging_attaches_filter_once():
    log = configure_logging("INFO", redact=True)
    log2 = configure_logging("INFO", redact=True)
    assert log is log2
    assert sum(isinstance(f, RedactingFilter) for f in log.filters) == 1

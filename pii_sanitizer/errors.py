"""Exception hierarchy for the PII sanitizer package.

All errors raised deliberately by this package derive from
:class:`SanitizerError` so callers can catch the whole family with a single
``except`` while still being able to distinguish specific failures.
"""

from __future__ import annotations


class SanitizerError(Exception):
    """Base class for every error raised by :mod:`pii_sanitizer`."""


class ExtractionError(SanitizerError):
    """Raised when text cannot be extracted from a PDF (corrupt/encrypted)."""


class OCRUnavailableError(ExtractionError):
    """Raised when a scanned/image PDF needs OCR but no OCR backend exists."""


class LeakDetectedError(SanitizerError):
    """Raised by the cloud gate when sanitized text still contains sensitive data.

    The message intentionally lists only *category names* (e.g. ``ssn``,
    ``email``) and never the offending values, so raising/logging this error
    can never itself leak PII.
    """


class VaultError(SanitizerError):
    """Raised for placeholder-vault problems (encryption, corruption, misuse)."""


class ConfigError(SanitizerError):
    """Raised when configuration is invalid or cannot be loaded."""

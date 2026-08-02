"""The cloud safety gate — the last line of defense before text leaves the box.

The gate re-scans *already sanitized* text for residual structured PII. It is
deliberately narrow and high-precision: it checks the identifier categories that
are both unambiguous and legally sensitive (SSN, EMAIL, PHONE, bank/routing/
account/loan numbers, EIN, street address). Names are excluded on purpose —
free-text names cannot be gated without unacceptable false positives, and the
detection layers already handle them upstream.

A gate hit means a detector missed something. In ``strict`` mode we raise rather
than send; that fail-closed posture is the whole point of privacy-by-design.

Crucially, gate output contains **category names only**, never the offending
value, so logging a gate failure can never itself leak PII.
"""

from __future__ import annotations

import re

from .errors import LeakDetectedError
from .vault import _PLACEHOLDER_RE

# Category -> pattern. Structured, unambiguous, must-never-leak identifiers.
_LEAK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ssn", re.compile(r"(?<!\d)\d{3}[-\s]\d{2}[-\s]\d{4}(?!\d)")),
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("phone", re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)")),
    ("ein", re.compile(r"(?<!\d)\d{2}-\d{7}(?!\d)")),
    (
        "account_number",
        re.compile(
            r"(?i)\b(?:aba|routing|account|acct|loan|mortgage)\s*"
            r"(?:transit\s*)?(?:number|no\.?|#|id)?\s*[:#-]?\s*"
            r"(?:x{2,}|\*{2,})?\d[\d -]{4,}\b"
        ),
    ),
    (
        "street_address",
        re.compile(
            r"\b\d{1,6}\s+[A-Z0-9][A-Za-z0-9.' -]{1,40}\s+"
            r"(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|"
            r"Court|Ct|Circle|Cir|Way|Place|Pl|Trail|Trl|Parkway|Pkwy)\b",
            re.I,
        ),
    ),
]


def find_leaks(text: str) -> list[str]:
    """Return the sorted, de-duplicated categories of residual PII in ``text``.

    Placeholders (``[LIKE_THIS]``) are stripped first so an ``[SSN_1]`` token is
    never mistaken for a real SSN.
    """
    scrubbed = _PLACEHOLDER_RE.sub(" ", str(text or ""))
    leaks = {name for name, pattern in _LEAK_PATTERNS if pattern.search(scrubbed)}
    return sorted(leaks)


def is_cloud_safe(text: str) -> bool:
    return not find_leaks(text)


def require_cloud_safe(text: str) -> None:
    """Raise :class:`LeakDetectedError` if any residual PII category is present.

    The exception message lists categories only — never values.
    """
    leaks = find_leaks(text)
    if leaks:
        raise LeakDetectedError("cloud gate blocked residual PII: " + ", ".join(leaks))

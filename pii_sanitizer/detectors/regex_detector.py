"""High-precision regex/pattern detectors for structured PII and labeled names.

This layer is deterministic, dependency-free and fast. It catches the
identifiers that NER is *bad* at (SSNs, routing/account/loan numbers, emails,
phones) and the mortgage-domain *labeled* names ("Borrower: John Smith") that
carry a known role — which is what lets us emit ``[BORROWER_1]`` rather than a
generic ``[PERSON_1]``.

It intentionally mirrors and extends the patterns already proven in the
project's ``privacy_filter.py`` so behavior stays consistent across the app.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Callable

from ..spans import Span

if TYPE_CHECKING:  # pragma: no cover
    from ..config import SanitizerConfig

# --- Structured identifiers: (entity_type, compiled_pattern, capture_group) ---
# capture_group is the group whose span becomes the redacted region. Group 0
# means the whole match; a labeled pattern uses a group so the label word
# ("Loan Number:") is preserved and only the value is redacted.

_SSN = re.compile(r"(?<!\d)\d{3}[-\s]\d{2}[-\s]\d{4}(?!\d)")
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE = re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)")
_EIN = re.compile(r"(?<!\d)\d{2}-\d{7}(?!\d)")

_ROUTING = re.compile(
    r"(?i)\b(?:aba|routing)\s*(?:transit\s*)?(?:number|no\.?|#)?\s*[:#-]?\s*(\d{9})\b"
)
_ACCOUNT = re.compile(
    r"(?i)\b(?:bank\s+)?(?:account|acct)\s*(?:number|no\.?|#)?\s*[:#-]?\s*"
    r"((?:x{2,}|\*{2,})?\d[\d -]{3,}\d)"
)
_LOAN_NUMBER = re.compile(
    r"(?i)\b(?:loan|mortgage|case|file)\s*(?:number|no\.?|#|id)\s*[:#-]?\s*"
    r"([A-Z0-9][A-Z0-9-]{4,})"
)
_PASSPORT = re.compile(
    r"(?i)\bpassport\s*(?:number|no\.?|#)?\s*[:#-]?\s*([A-Z0-9]{6,9})\b"
)
_DL = re.compile(
    r"(?i)\b(?:driver'?s?\s*licen[cs]e|dl)\s*(?:number|no\.?|#)?\s*[:#-]?\s*"
    r"([A-Z0-9]{5,15})\b"
)
_DOB = re.compile(
    r"(?i)\b(?:dob|date\s+of\s+birth|birth\s*date)\s*[:#-]?\s*"
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Z][a-z]+\s+\d{1,2},?\s+\d{4})"
)
_ADDRESS = re.compile(
    r"\b\d{1,6}\s+[A-Z0-9][A-Z0-9.' -]{1,55}\s+"
    r"(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|"
    r"Court|Ct|Circle|Cir|Way|Place|Pl|Trail|Trl|Parkway|Pkwy|Terrace|Ter|Highway|Hwy)"
    r"\b(?:[^\n,]{0,25})?(?:,\s*[A-Z][A-Z .'-]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?)?",
    re.I,
)
_ZIP = re.compile(r"(?<!\d)\d{5}(?:-\d{4})?(?!\d)")
_COUNTY = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+County\b")
_PROPERTY_ID = re.compile(
    r"(?i)\b(?:legal\s+description|parcel|apn|tax\s+id)\b[ \t]*(?:no\.?|number|#|:)?[ \t]*"
    r"([A-Z0-9][A-Z0-9.\-]{4,})"
)

# (entity_type, pattern, group_index)
_STRUCTURED: list[tuple[str, re.Pattern[str], int]] = [
    ("SSN", _SSN, 0),
    ("TAX_ID", _EIN, 0),
    ("EMAIL", _EMAIL, 0),
    ("PHONE", _PHONE, 0),
    ("ROUTING_NUMBER", _ROUTING, 1),
    ("ACCOUNT_NUMBER", _ACCOUNT, 1),
    ("LOAN_NUMBER", _LOAN_NUMBER, 1),
    ("PASSPORT", _PASSPORT, 1),
    ("DRIVERS_LICENSE", _DL, 1),
    ("DATE_OF_BIRTH", _DOB, 1),
    ("ADDRESS", _ADDRESS, 0),
    ("COUNTY", _COUNTY, 1),
    ("PROPERTY_IDENTIFIER", _PROPERTY_ID, 1),
]

# --- Labeled names carry a role. Map the label keyword to an entity type. ---
_ROLE_LABELS: list[tuple[str, str]] = [
    (r"co-?borrower", "COBORROWER"),
    (r"co-?applicant", "COBORROWER"),
    (r"borrower", "BORROWER"),
    (r"applicant", "BORROWER"),
    (r"seller", "SELLER"),
    (r"buyer", "BUYER"),
    (r"property\s+owner", "SELLER"),
    (r"listing\s+agent", "REALTOR"),
    (r"selling\s+agent", "REALTOR"),
    (r"buyer'?s?\s+agent", "REALTOR"),
    (r"realtor", "REALTOR"),
    (r"loan\s+officer", "LOAN_OFFICER"),
    (r"loan\s+originator", "LOAN_OFFICER"),
    (r"processor", "PROCESSOR"),
    (r"underwriter", "UNDERWRITER"),
    (r"employer", "EMPLOYER"),
    (r"lender", "LENDER"),
]

# Build one compiled pattern per role. The value is a 2–6 token capitalized name.
# Full name-word alternative comes first so "Smith" is not truncated to the
# single-initial "S" by ordered alternation.
_NAME_VALUE = r"([A-Z][A-Za-z'.-]+(?:[ \t]+(?:[A-Z][A-Za-z'.-]+|[A-Z]\.)){1,5})"
_ROLE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        entity,
        re.compile(
            rf"(?im)\b(?:{label})\b\s*(?:name)?\s*(?::|#|-|\bis\b)\s*{_NAME_VALUE}"
        ),
    )
    for label, entity in _ROLE_LABELS
]

# Company / employer names with legal suffixes (unlabeled but structurally clear).
_COMPANY = re.compile(
    r"\b([A-Z][A-Za-z&'.,-]*(?:[ \t]+[A-Z][A-Za-z&'.,-]*){0,5}"
    r"[ \t]+(?:LLC|L\.L\.C\.|Inc\.?|Incorporated|Corp\.?|Corporation|Company|"
    r"Co\.?|Bank|Mortgage|Lending|Financial|Realty|Realtors|Associates|Group|"
    r"Title|Escrow|Insurance))\b"
)


def _add(spans: list[Span], m: re.Match[str], group: int, entity: str) -> None:
    if group and m.group(group) is None:
        return
    start, end = m.span(group)
    if end <= start:
        return
    spans.append(
        Span(
            start=start,
            end=end,
            entity_type=entity,
            text=m.group(group),
            score=0.95,
            source="regex",
        )
    )


def detect(text: str, config: "SanitizerConfig | None" = None) -> list[Span]:
    """Return every regex/pattern span found in ``text`` (may overlap)."""
    src = str(text or "")
    enabled = set(config.enabled_entities) if config else None
    redact_money = bool(config and config.redact_money)
    spans: list[Span] = []

    def wanted(entity: str) -> bool:
        return enabled is None or entity in enabled

    # Role-typed labeled names first (highest domain value).
    for entity, pattern in _ROLE_PATTERNS:
        if not wanted(entity):
            continue
        for m in pattern.finditer(src):
            _add(spans, m, 1, entity)

    for entity, pattern, group in _STRUCTURED:
        if not wanted(entity):
            continue
        for m in pattern.finditer(src):
            _add(spans, m, group, entity)

    if wanted("COMPANY"):
        for m in _COMPANY.finditer(src):
            _add(spans, m, 1, "COMPANY")

    # ZIP is noisy on its own; only take it when it is not already inside an
    # address span (overlap resolution will drop the rest).
    if wanted("ZIP"):
        for m in _ZIP.finditer(src):
            _add(spans, m, 0, "ZIP")

    if redact_money:
        for m in re.finditer(r"(?<!\w)(?:USD\s*)?\$\s*\d[\d,]*(?:\.\d{2})?(?!\w)", src, re.I):
            _add(spans, m, 0, "OTHER")

    return spans

"""Local privacy filter for text that may be sent to an external AI service.

The original document and replacement map stay in memory on the local machine.
Cloud-bound text must pass ``find_sensitive_fragments`` after redaction.
"""

from __future__ import annotations

import re
from typing import Iterable


_PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z0-9_]*\]")

_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("ssn", re.compile(r"(?<!\d)\d{3}[-\s]\d{2}[-\s]\d{4}(?!\d)"), "[SSN]"),
    (
        "email",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
        "[EMAIL]",
    ),
    (
        "phone",
        re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)"),
        "[PHONE]",
    ),
    (
        "account",
        re.compile(
            r"(?i)\b(?:account|acct|routing|loan|case|file)\s*(?:number|no\.?|#)?\s*[:#-]?\s*"
            r"(?:x{2,}|\*{2,})?\d[\d -]{3,}\b"
        ),
        "[ACCOUNT_NUMBER]",
    ),
    (
        "dob",
        re.compile(
            r"(?i)\b(?:dob|date\s+of\s+birth|birth\s*date)\s*[:#-]?\s*"
            r"(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Z][a-z]+\s+\d{1,2},?\s+\d{4})"
        ),
        "[DATE_OF_BIRTH]",
    ),
    (
        "date",
        re.compile(
            r"(?<!\d)(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}(?!\d)"
            r"|\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
            r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
            r"Dec(?:ember)?)\s+\d{1,2},?\s+(?:19|20)\d{2}\b",
            re.I,
        ),
        "[EXACT_DATE]",
    ),
    (
        "money",
        re.compile(r"(?<!\w)(?:USD\s*)?\$\s*\d[\d,]*(?:\.\d{2})?(?!\w)", re.I),
        "[AMOUNT]",
    ),
    (
        "address",
        re.compile(
            r"\b\d{1,6}\s+[A-Z0-9][A-Z0-9.' -]{1,55}\s+"
            r"(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|Lane|Ln|"
            r"Court|Ct|Circle|Cir|Way|Place|Pl|Trail|Trl|Parkway|Pkwy)"
            r"\b(?:[^\n,]{0,25})?(?:,\s*[A-Z][A-Z .'-]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?)?",
            re.I,
        ),
        "[ADDRESS]",
    ),
    (
        "labeled_name",
        re.compile(
            r"(?m)\b(?i:borrower|co-borrower|applicant|buyer|seller|property\s+owner|"
            r"listing\s+agent|selling\s+agent|realtor|processor|underwriter)\s*"
            r"(?i:name)?\s*(?::|#|-|(?i:\bis\b))\s*[A-Z][A-Za-z'.-]+"
            r"(?:[ \t]+[A-Z][A-Za-z'.-]+){1,5}"
        ),
        "[PERSON]",
    ),
]

_INCOME_LINE_RE = re.compile(
    r"(?im)^.*\b(?:income|salary|wages?|earnings?|commission|bonus|monthly\s+gross)\b.*$"
)
_LEGAL_DESCRIPTION_RE = re.compile(
    r"(?im)^.*\b(?:legal\s+description|parcel|apn|tax\s+id|lot\s+\d+|block\s+\d+)\b.*$"
)
_LABELED_NAME_VALUE_RE = re.compile(
    r"(?m)\b(?i:borrower|co-borrower|applicant|buyer|seller|property\s+owner|"
    r"listing\s+agent|selling\s+agent|realtor|processor|underwriter)\s*"
    r"(?i:name)?\s*(?::|#|-|(?i:\bis\b))\s*"
    r"([A-Z][A-Za-z'.-]+(?:[ \t]+[A-Z][A-Za-z'.-]+){1,5})"
)


def _replace_known_values(text: str, known_values: Iterable[str] | None) -> tuple[str, dict[str, str]]:
    replacements: dict[str, str] = {}
    cleaned_values = sorted(
        {str(v).strip() for v in (known_values or []) if len(str(v).strip()) >= 3},
        key=len,
        reverse=True,
    )
    for index, value in enumerate(cleaned_values, start=1):
        placeholder = f"[KNOWN_VALUE_{index}]"
        pattern = re.compile(re.escape(value), re.I)
        if pattern.search(text):
            text = pattern.sub(placeholder, text)
            replacements[placeholder] = value
    return text, replacements


def redact_for_cloud(
    text: str,
    *,
    known_values: Iterable[str] | None = None,
    remove_income_lines: bool = True,
    remove_legal_descriptions: bool = True,
) -> tuple[str, dict[str, str], list[str]]:
    """Return sanitized text, a local-only replacement map, and remaining leak types."""
    original = str(text or "")
    discovered_names = [m.group(1) for m in _LABELED_NAME_VALUE_RE.finditer(original)]
    sanitized, replacements = _replace_known_values(
        original,
        list(known_values or []) + discovered_names,
    )

    if remove_income_lines:
        sanitized = _INCOME_LINE_RE.sub("[INCOME_INFORMATION_REDACTED]", sanitized)
    if remove_legal_descriptions:
        sanitized = _LEGAL_DESCRIPTION_RE.sub("[PROPERTY_IDENTIFIER_REDACTED]", sanitized)

    counters: dict[str, int] = {}
    for kind, pattern, base_placeholder in _PATTERNS:
        def _replacement(match: re.Match[str]) -> str:
            counters[kind] = counters.get(kind, 0) + 1
            placeholder = base_placeholder[:-1] + f"_{counters[kind]}]"
            replacements[placeholder] = match.group(0)
            return placeholder

        sanitized = pattern.sub(_replacement, sanitized)

    sanitized = re.sub(r"[ \t]+", " ", sanitized)
    sanitized = re.sub(r"\n{3,}", "\n\n", sanitized).strip()
    leaks = find_sensitive_fragments(sanitized)
    return sanitized, replacements, leaks


def find_sensitive_fragments(text: str) -> list[str]:
    """Return sensitive-data categories still visible outside approved placeholders."""
    scrubbed = _PLACEHOLDER_RE.sub("", str(text or ""))
    leaks = [kind for kind, pattern, _ in _PATTERNS if pattern.search(scrubbed)]
    if _INCOME_LINE_RE.search(scrubbed):
        leaks.append("income")
    if _LEGAL_DESCRIPTION_RE.search(scrubbed):
        leaks.append("property_identifier")
    return sorted(set(leaks))


def require_cloud_safe(text: str) -> None:
    leaks = find_sensitive_fragments(text)
    if leaks:
        raise ValueError("Cloud privacy gate blocked: " + ", ".join(leaks))


def restore_local_placeholders(text: str, replacements: dict[str, str]) -> str:
    """Restore cloud-safe placeholders after the response returns locally."""
    restored = str(text or "")
    for placeholder in sorted(replacements, key=len, reverse=True):
        restored = re.sub(
            re.escape(placeholder),
            lambda _match, value=replacements[placeholder]: value,
            restored,
            flags=re.I,
        )
    return restored


def has_unresolved_placeholders(text: str) -> bool:
    return bool(_PLACEHOLDER_RE.search(str(text or "")))

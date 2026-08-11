"""Local privacy filter for text that may be sent to an external AI service.

The original document and replacement map stay in memory on the local machine.
Cloud-bound text must pass ``find_sensitive_fragments`` after redaction.
"""

from __future__ import annotations

import re
from typing import Iterable


# Security policy appended to approval-analysis system prompts.  This is kept
# beside the executable privacy gate so prompt behavior cannot drift away from
# the local redaction boundary that enforces it.
SECURE_APPROVAL_INTELLIGENCE_PROMPT = """
You are working inside a mortgage approval processing application. Apply these
rules only after the application has locally removed borrower-sensitive data.
Never request, reconstruct, infer, retain, log, score, or learn from borrower
names, contact details, identifiers, addresses, account data, income figures,
or any other private borrower content. Work only with the sanitized lender
name, de-identified document-format signals, and de-identified condition-language
patterns. Preserve redaction placeholders and never treat them as learnable data.

For lender accuracy, evaluate how reliably the sanitized lender format was
parsed. Any accuracy observation must be associated only with the lender name
and aggregate, de-identified format outcomes. It must never contain document
text, condition text, borrower data, replacement maps, or document identifiers.
Lender accuracy rankings are private to the uploading processor and must never
be presented as public rankings or shared across processors.

For condition ownership, classify the responsible owner from de-identified
language patterns into Borrower, Lender, or Broker / Loan Officer. Language such
as "provide updated paystubs" generally signals Borrower; lender-performed
verification such as "verification of employment" generally signals Lender;
and requirements for the originating company or its licensing/good standing
generally signal Broker / Loan Officer. Classify silently when confidence is
high. Mark borderline or ambiguous conditions as Best Guess so the processor
can confirm them. A correction may contribute only a de-identified language
pattern and corrected owner; never retain the original condition or private
content as learning data.
""".strip()


def secure_approval_system_prompt(system: str) -> str:
    """Attach the de-identified approval policy to a task-specific prompt."""
    return f"{SECURE_APPROVAL_INTELLIGENCE_PROMPT}\n\n{str(system or '').strip()}".strip()


_PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z0-9_]*\]")

_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("ssn", re.compile(r"(?<!\d)\d{3}[-\s]\d{2}[-\s]\d{4}(?!\d)"), "[SSN]"),
    (
        "ein",
        re.compile(
            r"(?i)\b(?:ein|fein|federal\s+(?:tax\s+)?id|taxpayer\s+id)\s*"
            r"(?:number|no\.?|#)?\s*[:#-]?\s*\d{2}[-\s]?\d{7}\b"
        ),
        "[EIN]",
    ),
    (
        "government_id",
        re.compile(
            r"(?i)\b(?:driver'?s?\s+licen[cs]e|state\s+id|passport)\s*"
            r"(?:number|no\.?|#)?\s*[:#-]?\s*[A-Z0-9][A-Z0-9-]{5,19}\b"
        ),
        "[GOVERNMENT_ID]",
    ),
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

# Value-level redaction: keep the skeleton word ("income", "parcel") so the
# document still reads as a document, but strip the sensitive figure/identifier
# next to it. Group 1 is kept verbatim; group 2 (the value) is replaced.
_INCOME_VALUE_RE = re.compile(
    r"(?i)(\b(?:income|salary|wages?|earnings?|commission|bonus|monthly\s+gross)\b"
    r"(?:[^\n\d$]{0,24}?))"
    r"(\$?[ \t]*\d[\d,]*(?:\.\d{2})?)"
)
_LEGAL_VALUE_RE = re.compile(
    r"(?i)(\b(?:legal\s+description|parcel|apn|tax\s+id)\b[ \t]*(?:no\.?|number|#|:)?[ \t]*)"
    r"([A-Z0-9][A-Z0-9.\-]{4,})"
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
        sanitized = _INCOME_VALUE_RE.sub(lambda m: m.group(1) + "[INCOME_AMOUNT]", sanitized)
    if remove_legal_descriptions:
        sanitized = _LEGAL_VALUE_RE.sub(lambda m: m.group(1) + "[PROPERTY_IDENTIFIER]", sanitized)

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


def redact_for_cloud_resilient(
    text: str,
    *,
    known_values: Iterable[str] | None = None,
) -> tuple[str, dict[str, str], list[str], list[str]]:
    """Redact aggressively and return verified-safe usable text when possible.

    The third return value lists categories that needed the second, destructive
    redaction pass. The fourth contains categories that still remain and must
    block transport. Residual values are never restored after this pass.
    """
    sanitized, replacements, leaks = redact_for_cloud(text, known_values=known_values)
    forced = set(leaks)
    # A replacement can expose a second match behind it in flattened PDF text.
    # Iterate until stable instead of assuming one destructive pass is enough.
    for _pass in range(12):
        current = find_sensitive_fragments(sanitized)
        if not current:
            break
        forced.update(current)
        before = sanitized
        for kind, pattern, _placeholder in _PATTERNS:
            if kind in current:
                sanitized = pattern.sub(f"[{kind.upper()}_REDACTED]", sanitized)
        if "income" in current:
            sanitized = _INCOME_VALUE_RE.sub(
                lambda match: match.group(1) + "[INCOME_INFORMATION_REDACTED]",
                sanitized,
            )
        if "property_identifier" in current:
            sanitized = _LEGAL_VALUE_RE.sub(
                lambda match: match.group(1) + "[PROPERTY_IDENTIFIER_REDACTED]",
                sanitized,
            )
        if sanitized == before:
            break

    remaining = find_sensitive_fragments(sanitized)
    if "labeled_name" in remaining:
        # Role labels can repeatedly bind to later Title Case condition text
        # after placeholders are ignored by the leak checker. Neutralize only
        # the residual role labels; the local result keeps the original words.
        sanitized = re.sub(
            r"(?i)\b(?:borrower|co-borrower|applicant|buyer|seller|property\s+owner|"
            r"listing\s+agent|selling\s+agent|realtor|processor|underwriter)\b",
            "[PARTY_ROLE_REDACTED]",
            sanitized,
        )
        forced.add("labeled_name")

    remaining = find_sensitive_fragments(sanitized)
    if remaining:
        # Keep every safe line instead of discarding the entire approval. This
        # is deliberately lossy: quarantined lines remain available only to the
        # local parser and are never included in the cloud request.
        safe_lines = []
        for line in sanitized.splitlines():
            line_leaks = find_sensitive_fragments(line)
            if line_leaks:
                forced.update(line_leaks)
            else:
                safe_lines.append(line)
        sanitized = "\n[SAFE_SECTION_BREAK]\n".join(safe_lines).strip()
        remaining = find_sensitive_fragments(sanitized)
    if remaining:
        # Fail closed on the unsafe fragments, not on the entire AI operation.
        # Returning an empty verified-safe slice allows the other sanitized
        # input (document or locally extracted condition rows) to proceed.
        forced.update(remaining)
        sanitized = ""
        remaining = []
    return sanitized, replacements, sorted(forced), remaining


def find_sensitive_fragments(text: str) -> list[str]:
    """Return sensitive-data categories still visible outside approved placeholders."""
    scrubbed = _PLACEHOLDER_RE.sub("", str(text or ""))
    leaks = [kind for kind, pattern, _ in _PATTERNS if pattern.search(scrubbed)]
    if _INCOME_VALUE_RE.search(scrubbed):
        leaks.append("income")
    if _LEGAL_VALUE_RE.search(scrubbed):
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


_SOURCE_PROPER_NAME_RE = re.compile(
    r"\b[A-Z][a-zA-Z'.-]{1,30}(?:[ \t]+[A-Z][a-zA-Z'.-]{1,30}){1,4}\b"
)
_PROPER_NAME_EXCLUSIONS = {
    "Approval Letter",
    "Closing Disclosure",
    "Loan Estimate",
    "Purchase Contract",
    "Bank Statement",
    "Credit Report",
    "Homeowners Insurance",
    "Social Security",
    "High Confidence",
    "Best Guess",
}


def redact_gemini_output(text: str, *, source_text: str = "") -> str:
    """Redact sensitive values from a Gemini response before callers receive it."""
    source = str(source_text or "")
    known_values = [
        match.group(0)
        for match in _SOURCE_PROPER_NAME_RE.finditer(source)
        if match.group(0) not in _PROPER_NAME_EXCLUSIONS
    ]
    _, source_replacements, _ = redact_for_cloud(source, known_values=known_values)
    source_values = list(source_replacements.values()) + known_values
    sanitized, _, _ = redact_for_cloud(str(text or ""), known_values=source_values)
    return sanitized

"""Drop-in shim matching the project's existing ``privacy_filter`` API.

Your ``cloud_client.py`` already calls ``redact_for_cloud`` /
``restore_local_placeholders`` / ``require_cloud_safe`` and passes a plain
``{placeholder: original}`` dict around. This module re-implements those exact
signatures on top of the new engine, so you can switch with a one-line import
change and get NER + OCR + typed placeholders for free:

    # before
    from privacy_filter import redact_for_cloud, restore_local_placeholders
    # after
    from pii_sanitizer.integration import redact_for_cloud, restore_local_placeholders

The returned mapping is still a local-only dict — never send it to Gemini.
"""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable

from .config import SanitizerConfig, load_config
from .gate import find_leaks
from .sanitizer import sanitize_text
from .vault import _PLACEHOLDER_RE
from privacy_filter import (
    find_sensitive_fragments as _legacy_find_sensitive_fragments,
    redact_for_cloud as _legacy_redact_for_cloud,
    redact_for_cloud_resilient as _legacy_redact_for_cloud_resilient,
    redact_gemini_output as _legacy_redact_gemini_output,
    secure_approval_system_prompt,
)

__all__ = [
    "redact_for_cloud",
    "redact_for_cloud_resilient",
    "restore_local_placeholders",
    "require_cloud_safe",
    "find_sensitive_fragments",
    "has_unresolved_placeholders",
    "redact_gemini_output",
    "secure_approval_system_prompt",
]


_PARTY_LABEL = r"(?:co[\s-]?borrower|borrower|co[\s-]?applicant|applicant|buyer|seller|mortgagor)s?(?:\s+names?)?"
_PARTY_LABEL_LINE = re.compile(rf"^\s*{_PARTY_LABEL}(?:\s*[:/&,]?\s*{_PARTY_LABEL})*\s*:?\s*$", re.IGNORECASE)
_PARTY_LABEL_INLINE = re.compile(rf"^\s*{_PARTY_LABEL}\s*:\s*(.+)$", re.IGNORECASE)
_NAME_WORD = re.compile(r"^[A-Z][a-zA-Z'\-]+\.?$|^[A-Z]\.?$")


def _name_runs(line: str) -> list[str]:
    """Split a line into runs of capitalized name-like words ("Alex Sample Taylor Sample" -> 1 run)."""
    runs, current = [], []
    for word in re.split(r"[\s,&]+", line.strip()):
        if word and _NAME_WORD.match(word) and word.lower() not in {"and", "the", "loan", "number"}:
            current.append(word)
        else:
            if current:
                runs.append(current)
            current = []
    if current:
        runs.append(current)
    return [" ".join(r) for r in runs if 2 <= len(r) <= 8]


def labeled_party_names(text: str) -> list[str]:
    """Names printed under/after Borrower, Co-Borrower, Applicant, Buyer, Seller labels.

    Name detectors miss names on the line below a label, or side by side in
    OCR'd columns, so collect them by layout and force-redact them.
    """
    names: list[str] = []
    lines = [ln for ln in (text or "").splitlines()]
    for i, line in enumerate(lines):
        inline = _PARTY_LABEL_INLINE.match(line)
        if inline:
            names.extend(_name_runs(inline.group(1)))
            continue
        if not _PARTY_LABEL_LINE.match(line):
            continue
        labels = len(re.findall(_PARTY_LABEL, line, re.IGNORECASE))
        nxt = next((ln for ln in lines[i + 1:i + 3] if ln.strip()), "")
        for run in _name_runs(nxt):
            words = run.split()
            # Two labels side by side ("BORROWER CO-BORROWER") -> split the run in half.
            if labels >= 2 and len(words) >= 4 and len(words) % labels == 0:
                size = len(words) // labels
                names.extend(" ".join(words[j:j + size]) for j in range(0, len(words), size))
            names.append(run)
    for match in _ROLE_NAME.finditer(text or ""):
        words = match.group(1).split()
        if words[0].strip(".") not in _NOT_NAME_WORDS and not any(w in _NOT_NAME_WORDS for w in words):
            names.append(" ".join(words))
    seen, unique = set(), []
    for name in names:
        if name.lower() not in seen:
            seen.add(name.lower())
            unique.append(name)
    return unique


# A person's name right after a role word: "donor Elena Vasquez", "Loan officer Jordan
# Whitfield", "Seller Gregory Tan to repair". Header words keep "Borrower Conditions" intact.
_ROLE_NAME = re.compile(
    r"\b(?i:gift\s+donor|donor|loan\s+officer|loan\s+originator|processor|underwriter|closer|"
    r"listing\s+agent|selling\s+agent|agent|realtor|attorney|title\s+officer|escrow\s+officer|"
    r"co[\s-]?borrower|borrower|seller|buyer|applicant|signed\s+by|prepared\s+for|attn:?|attention|"
    r"dear|mr\.?|mrs\.?|ms\.?|dr\.?)\s+((?:[A-Z][a-z'\-]+|[A-Z]\.)(?:\s+(?:[A-Z][a-z'\-]+|[A-Z]\.)){1,3})"
)
_NOT_NAME_WORDS = {
    "Conditions", "Condition", "Requirements", "Section", "Certification", "Disclosure", "Insurance",
    "Credit", "Agreement", "Signature", "Signatures", "Information", "Name", "Names", "Address",
    "Package", "Letter", "Statement", "Statements", "Income", "Assets", "Closing", "Docs",
    "Documents", "Authorization", "Contact", "Provide", "To", "Must", "Shall", "Will", "Final",
    "Prior", "Funding", "Approval", "Loan", "Funds", "Paid", "Concessions", "Contribution", "Acknowledgment",
}
_NUMBER_LABEL = re.compile(r"\b(?:loan\s*(?:number|no\.?|#)|account\s*(?:number|no\.?|#)?|ssn|social\s+security(?:\s+number)?)\b",
                           re.IGNORECASE)
_CORP_SUFFIX = re.compile(r"[,\s]+(?:llc|l\.l\.c\.|inc\.?|incorporated|corp\.?|corporation|co\.|ltd\.?|lp|llp)\s*$",
                          re.IGNORECASE)


def labeled_numbers(text: str) -> list[str]:
    """Account/loan/SSN numbers printed below their label (column layouts).

    "LOAN NUMBER PROPERTY" / "7744120931 2218 Willow ..." -> ["7744120931"]
    """
    values: list[str] = []
    lines = (text or "").splitlines()
    for i, line in enumerate(lines):
        if not _NUMBER_LABEL.search(line) or re.search(r"\d{4,}", line):
            continue
        nxt = next((ln for ln in lines[i + 1:i + 3] if ln.strip()), "")
        values.extend(tok for tok in re.findall(r"[A-Z0-9][A-Z0-9\-]{4,}", nxt)
                      if len(re.sub(r"\D", "", tok)) >= 5)
    return list(dict.fromkeys(values))


def expand_known_values(values: Iterable[str]) -> list[str]:
    """Add the suffix-less form of company names ("Acme Logistics LLC" -> "Acme Logistics")."""
    out: list[str] = []
    for value in values or []:
        value = str(value or "").strip()
        if not value:
            continue
        out.append(value)
        stem = _CORP_SUFFIX.sub("", value).strip()
        if stem != value and len(stem.split()) >= 2:
            out.append(stem)
    return list(dict.fromkeys(out))


def redact_for_cloud(
    text: str,
    *,
    known_values: Iterable[str] | None = None,
    remove_income_lines: bool = True,
    remove_legal_descriptions: bool = True,
    config: SanitizerConfig | None = None,
) -> tuple[str, dict[str, str], list[str]]:
    """Compatible with ``privacy_filter.redact_for_cloud``.

    Returns ``(sanitized_text, {placeholder: original}, residual_leak_categories)``.
    The ``remove_income_lines`` / ``remove_legal_descriptions`` flags are honored
    via config (property identifiers are always redacted; income amounts are kept
    unless ``config.redact_money`` is set).
    """
    cfg = replace(config or load_config(), strict_gate=False)
    known_values = expand_known_values(
        list(known_values or []) + labeled_party_names(text) + labeled_numbers(text))
    result = sanitize_text(text, config=cfg, known_values=known_values)
    mapping = result.vault.mapping()
    sanitized, legacy_mapping, _ = _legacy_redact_for_cloud(
        result.sanitized_text,
        remove_income_lines=remove_income_lines,
        remove_legal_descriptions=remove_legal_descriptions,
    )
    mapping.update(legacy_mapping)
    leaks = find_sensitive_fragments(sanitized)
    return sanitized, mapping, leaks


def redact_for_cloud_resilient(
    text: str,
    *,
    known_values: Iterable[str] | None = None,
) -> tuple[str, dict[str, str], list[str], list[str]]:
    """Run the typed sanitizer, then the proven lossy fallback if needed.

    The first pass adds typed placeholders and optional NER. The legacy second
    pass retains the application's income/property rules and its safe-line
    quarantine behavior. Only categories, never values, are returned as errors.
    """
    sanitized, replacements, initial_leaks = redact_for_cloud(
        text,
        known_values=known_values,
    )
    forced = set(initial_leaks)
    if initial_leaks:
        sanitized, fallback_replacements, fallback_forced, _ = (
            _legacy_redact_for_cloud_resilient(sanitized)
        )
        replacements.update(fallback_replacements)
        forced.update(fallback_forced)

    remaining = find_sensitive_fragments(sanitized)
    if remaining:
        # The legacy helper is deliberately destructive on its final pass. Run
        # it once more if a detector exposed a second match behind a replacement.
        sanitized, fallback_replacements, fallback_forced, remaining = (
            _legacy_redact_for_cloud_resilient(sanitized)
        )
        replacements.update(fallback_replacements)
        forced.update(fallback_forced)
    return sanitized, replacements, sorted(forced), sorted(set(remaining))


def restore_local_placeholders(text: str, replacements: dict[str, str]) -> str:
    """Compatible with ``privacy_filter.restore_local_placeholders``.

    Restores from a plain dict (longest placeholder first).
    """
    restored = str(text or "")
    for placeholder in sorted(replacements, key=len, reverse=True):
        restored = re.sub(
            re.escape(placeholder),
            lambda _match, value=replacements[placeholder]: value,
            restored,
            flags=re.I,
        )
    return restored


def require_cloud_safe(text: str) -> None:
    """Compatible with ``privacy_filter.require_cloud_safe`` (raises on leak)."""
    leaks = find_sensitive_fragments(text)
    if leaks:
        # cloud_client historically catches ValueError from the privacy gate.
        raise ValueError("Cloud privacy gate blocked: " + ", ".join(leaks))


def find_sensitive_fragments(text: str) -> list[str]:
    """Compatible with ``privacy_filter.find_sensitive_fragments``."""
    return sorted(set(find_leaks(text)) | set(_legacy_find_sensitive_fragments(text)))


def has_unresolved_placeholders(text: str) -> bool:
    """True if any ``[LIKE_THIS]`` placeholder remains in ``text``."""
    return bool(_PLACEHOLDER_RE.search(str(text or "")))


def redact_gemini_output(text: str, *, source_text: str = "") -> str:
    """Compatible with ``privacy_filter.redact_gemini_output``.

    Defense-in-depth: scrub the model's *response* using values learned from the
    source, in case a placeholder was echoed back with an original nearby.
    """
    cfg = replace(load_config(), strict_gate=False)
    source = str(source_text or "")
    known: list[str] = []
    if source:
        src_result = sanitize_text(source, config=cfg)
        known = expand_known_values(list(src_result.vault.mapping().values())
                                    + labeled_party_names(source) + labeled_numbers(source))
    result = sanitize_text(str(text or ""), config=cfg, known_values=known)
    return _legacy_redact_gemini_output(result.sanitized_text, source_text=source_text)

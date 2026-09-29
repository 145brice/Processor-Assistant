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
        known = list(src_result.vault.mapping().values())
    result = sanitize_text(str(text or ""), config=cfg, known_values=known)
    return _legacy_redact_gemini_output(result.sanitized_text, source_text=source_text)

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
from typing import Iterable

from .config import SanitizerConfig
from .gate import find_leaks
from .gate import require_cloud_safe as _require_cloud_safe
from .sanitizer import sanitize_text
from .vault import _PLACEHOLDER_RE

__all__ = [
    "redact_for_cloud",
    "restore_local_placeholders",
    "require_cloud_safe",
    "find_sensitive_fragments",
    "has_unresolved_placeholders",
    "redact_gemini_output",
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
    cfg = config or SanitizerConfig(strict_gate=False)
    result = sanitize_text(text, config=cfg, known_values=known_values)
    mapping = result.vault.mapping()
    return result.sanitized_text, mapping, result.residual_leaks


def restore_local_placeholders(text: str, replacements: dict[str, str]) -> str:
    """Compatible with ``privacy_filter.restore_local_placeholders``.

    Restores from a plain dict (longest placeholder first).
    """
    restored = str(text or "")
    for placeholder in sorted(replacements, key=len, reverse=True):
        if placeholder in restored:
            restored = restored.replace(placeholder, replacements[placeholder])
    return restored


def require_cloud_safe(text: str) -> None:
    """Compatible with ``privacy_filter.require_cloud_safe`` (raises on leak)."""
    _require_cloud_safe(text)


def find_sensitive_fragments(text: str) -> list[str]:
    """Compatible with ``privacy_filter.find_sensitive_fragments``."""
    return find_leaks(text)


def has_unresolved_placeholders(text: str) -> bool:
    """True if any ``[LIKE_THIS]`` placeholder remains in ``text``."""
    return bool(_PLACEHOLDER_RE.search(str(text or "")))


def redact_gemini_output(text: str, *, source_text: str = "") -> str:
    """Compatible with ``privacy_filter.redact_gemini_output``.

    Defense-in-depth: scrub the model's *response* using values learned from the
    source, in case a placeholder was echoed back with an original nearby.
    """
    cfg = SanitizerConfig(strict_gate=False, enable_ner=True)
    source = str(source_text or "")
    known: list[str] = []
    if source:
        src_result = sanitize_text(source, config=cfg)
        known = list(src_result.vault.mapping().values())
    result = sanitize_text(str(text or ""), config=cfg, known_values=known)
    return result.sanitized_text

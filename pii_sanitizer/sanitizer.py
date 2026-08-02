"""The orchestrator: PDF/text in, sanitized text + Vault out.

Pipeline
--------
1. (PDF path) Extract text locally, OCR'ing scanned pages.
2. Run every enabled detector (regex, NER, barcode payloads) to get spans.
3. Fold in caller-supplied ``known_values`` (e.g. borrower names from your DB)
   as forced, exact-match spans — the most reliable signal of all.
4. Resolve overlaps, keeping the strongest span per region.
5. Replace right-to-left, minting deterministic placeholders from the Vault.
6. Run the cloud gate; fail closed in strict mode.

Only the returned ``sanitized_text`` is ever meant to leave the machine. The
returned :class:`~pii_sanitizer.vault.Vault` holds the reverse map and stays
local. Call :func:`restore` on the LLM's response to put the originals back.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Iterable, Mapping

from .config import SanitizerConfig
from .detectors import barcode_detector, ner_detector, regex_detector
from .extraction import ExtractionResult, extract
from .gate import find_leaks, require_cloud_safe
from .spans import Span, resolve_overlaps
from .vault import Vault

_log = logging.getLogger("pii_sanitizer.sanitizer")

_WS = re.compile(r"[ \t]+")
_BLANK_LINES = re.compile(r"\n{3,}")


@dataclass(slots=True)
class SanitizationResult:
    """Outcome of sanitizing one document."""

    sanitized_text: str
    vault: Vault
    entity_counts: dict[str, int] = field(default_factory=dict)
    residual_leaks: list[str] = field(default_factory=list)
    extraction: ExtractionResult | None = None

    @property
    def is_cloud_safe(self) -> bool:
        return not self.residual_leaks


def _known_value_spans(text: str, known_values: Mapping[str, str] | Iterable[str] | None) -> list[Span]:
    """Force-redact caller-supplied values (exact, case-insensitive matches)."""
    if not known_values:
        return []
    if isinstance(known_values, Mapping):
        items = list(known_values.items())
    else:
        items = [(v, "PERSON") for v in known_values]
    # Longest first so "John Q. Smith" wins over "John".
    items = sorted(
        ((str(v).strip(), t) for v, t in items if len(str(v).strip()) >= 3),
        key=lambda it: len(it[0]),
        reverse=True,
    )
    spans: list[Span] = []
    for value, entity in items:
        for m in re.finditer(re.escape(value), text, flags=re.I):
            spans.append(
                Span(
                    start=m.start(),
                    end=m.end(),
                    entity_type=(entity or "PERSON").upper(),
                    text=m.group(0),
                    score=1.0,
                    source="known_value",
                )
            )
    return spans


def sanitize_text(
    text: str,
    *,
    config: SanitizerConfig | None = None,
    vault: Vault | None = None,
    known_values: Mapping[str, str] | Iterable[str] | None = None,
    extra_spans: Iterable[Span] | None = None,
) -> SanitizationResult:
    """Sanitize a raw text string. This is the pure, dependency-light core."""
    cfg = config or SanitizerConfig()
    src = str(text or "")
    vault = vault if vault is not None else Vault()

    spans: list[Span] = []
    spans.extend(_known_value_spans(src, known_values))
    if extra_spans:
        spans.extend(extra_spans)
    if cfg.enable_regex:
        spans.extend(regex_detector.detect(src, cfg))
    if cfg.enable_ner:
        spans.extend(ner_detector.detect(src, cfg))

    resolved = resolve_overlaps(spans)

    # Replace right-to-left so earlier offsets stay valid as we mutate.
    out = src
    counts: dict[str, int] = {}
    for span in sorted(resolved, key=lambda s: s.start, reverse=True):
        placeholder = vault.placeholder_for(span.entity_type, span.text)
        out = out[: span.start] + placeholder + out[span.end :]
        counts[span.entity_type] = counts.get(span.entity_type, 0) + 1

    out = _WS.sub(" ", out)
    out = _BLANK_LINES.sub("\n\n", out).strip()

    leaks = find_leaks(out)
    if leaks and cfg.strict_gate:
        # Message lists categories only — safe to log/raise.
        require_cloud_safe(out)

    return SanitizationResult(
        sanitized_text=out,
        vault=vault,
        entity_counts=counts,
        residual_leaks=leaks,
    )


def sanitize_pdf(
    pdf_bytes: bytes,
    *,
    config: SanitizerConfig | None = None,
    vault: Vault | None = None,
    known_values: Mapping[str, str] | Iterable[str] | None = None,
) -> SanitizationResult:
    """Extract, OCR if needed, scan visual codes, then sanitize the text."""
    cfg = config or SanitizerConfig()
    extraction = extract(pdf_bytes, cfg)

    extra: list[Span] = []
    if cfg.enable_barcode and extraction.page_images:
        codes = barcode_detector.scan_images(extraction.page_images, config=cfg)
        if codes:
            _log.info("visual codes found: %d", len(codes))
            extra.extend(barcode_detector.spans_for_payloads(extraction.text, codes))

    result = sanitize_text(
        extraction.text,
        config=cfg,
        vault=vault,
        known_values=known_values,
        extra_spans=extra,
    )
    result.extraction = extraction
    return result


def restore(text: str, vault: Vault) -> str:
    """Restore original values into an LLM response using the local Vault."""
    return vault.restore(text)

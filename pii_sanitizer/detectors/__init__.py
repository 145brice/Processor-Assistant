"""Detector plugins. Each exposes ``detect(text, config) -> list[Span]``.

Detectors are independent and additive: the sanitizer runs every enabled one
and merges their spans through :func:`pii_sanitizer.spans.resolve_overlaps`.
Optional detectors (NER, barcode) degrade to an empty list when their heavy
third-party dependencies are not installed, so the core never hard-fails.
"""

from __future__ import annotations

from . import barcode_detector, ner_detector, regex_detector

__all__ = ["regex_detector", "ner_detector", "barcode_detector"]

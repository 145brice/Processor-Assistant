"""QR-code / barcode detection on rendered PDF page images.

Signatures, QR codes and barcodes are *visual* — they never appear in the
extracted text stream, so they can never leak through the text-only channel we
send to the LLM. This detector exists for two remaining reasons:

1. **Payload safety.** A QR code or Code-128 barcode can *encode* PII (a portal
   URL with a token, an account number). We decode them and, if the decoded
   payload also appears in the document text, redact that text.
2. **Audit trail.** We record the count/type of visual codes and signature-like
   regions found, which the compliance report needs.

Requires ``pyzbar`` + ``Pillow`` (optional). Absent those, returns empty results
and the sanitizer proceeds — visual codes are non-leaking by construction.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

from ..spans import Span

if TYPE_CHECKING:  # pragma: no cover
    from ..config import SanitizerConfig

_log = logging.getLogger("pii_sanitizer.barcode")


@dataclass(frozen=True, slots=True)
class DecodedCode:
    kind: str          # "QR_CODE" or "BARCODE"
    payload: str       # decoded text (may be empty for unreadable codes)
    page: int


def scan_images(images: Sequence[object], *, config: "SanitizerConfig | None" = None) -> list[DecodedCode]:
    """Decode QR/barcodes from a sequence of PIL images (one per page).

    ``images`` are PIL ``Image`` objects; we accept ``object`` to avoid a hard
    Pillow import at module load.
    """
    if config is not None and not config.enable_barcode:
        return []
    try:
        from pyzbar import pyzbar  # type: ignore
    except Exception as exc:
        _log.info("pyzbar unavailable (%s); skipping visual code scan.", type(exc).__name__)
        return []

    found: list[DecodedCode] = []
    for page_index, image in enumerate(images, start=1):
        try:
            for code in pyzbar.decode(image):
                raw = code.type or ""
                kind = "QR_CODE" if raw.upper() == "QRCODE" else "BARCODE"
                payload = ""
                try:
                    payload = code.data.decode("utf-8", "replace")
                except Exception:
                    payload = ""
                found.append(DecodedCode(kind=kind, payload=payload, page=page_index))
        except Exception as exc:  # pragma: no cover - decoder robustness
            _log.debug("code scan failed on page %d: %s", page_index, exc)
    return found


def spans_for_payloads(text: str, codes: Sequence[DecodedCode]) -> list[Span]:
    """Return spans for any decoded code payload that appears in ``text``."""
    src = str(text or "")
    spans: list[Span] = []
    for code in codes:
        payload = (code.payload or "").strip()
        if len(payload) < 4:
            continue
        start = src.find(payload)
        while start != -1:
            spans.append(
                Span(
                    start=start,
                    end=start + len(payload),
                    entity_type=code.kind,
                    text=payload,
                    score=0.99,
                    source="barcode",
                )
            )
            start = src.find(payload, start + len(payload))
    return spans


def detect(text: str, config: "SanitizerConfig | None" = None) -> list[Span]:
    """Text-only interface (no-op). Visual scanning uses :func:`scan_images`."""
    return []

"""PDF text extraction with automatic image-vs-text detection and OCR.

Strategy, per page:

* Pull the embedded text layer with ``pypdf`` (fast, exact, preserves order).
* If a page yields fewer than ``min_embedded_chars`` characters it is treated as
  image-based (scanned). We render it with PyMuPDF and OCR it with Tesseract.
* Hybrid documents (a searchable header row over a scanned body — common on
  lender approval sheets) keep both layers so no condition is lost.

Everything runs **locally and in memory**. Page bytes are never written to disk.
Optional deps (``pymupdf``, ``pytesseract``, ``Pillow``) gate the OCR path; when
they are absent, a scanned page raises :class:`OCRUnavailableError` in strict
mode so we fail closed instead of silently sending an empty document.
"""

from __future__ import annotations

import io
import logging
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .errors import ExtractionError, OCRUnavailableError

if TYPE_CHECKING:  # pragma: no cover
    from .config import SanitizerConfig

_log = logging.getLogger("pii_sanitizer.extraction")


@dataclass(slots=True)
class ExtractionResult:
    text: str
    page_count: int
    ocr_page_numbers: list[int] = field(default_factory=list)
    is_image_based: bool = False
    # PIL images for pages that were rendered, for optional barcode/QR scanning.
    page_images: list[object] = field(default_factory=list)


def _resolve_tesseract(config: "SanitizerConfig | None") -> None:
    """Point pytesseract at a tesseract binary, honoring config/env/known paths."""
    try:
        import pytesseract  # type: ignore
    except Exception:
        return
    configured = (config.tesseract_cmd if config else None) or os.getenv("TESSERACT_CMD") or ""
    candidates = [
        configured,
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe"),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            return


def extract(pdf_bytes: bytes, config: "SanitizerConfig | None" = None) -> ExtractionResult:
    """Extract reading-ordered text from ``pdf_bytes``, OCR'ing scanned pages."""
    if not pdf_bytes:
        raise ExtractionError("empty PDF bytes")

    min_chars = config.min_embedded_chars if config else 50
    ocr_enabled = config.ocr_enabled if config else True
    want_images = bool(config is None or config.enable_barcode)

    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover - pypdf is a core dep
        raise ExtractionError("pypdf is required for extraction") from exc

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as exc:
        raise ExtractionError(f"could not open PDF: {exc}") from exc

    page_texts: list[str] = []
    scanned_pages: list[int] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            embedded = (page.extract_text() or "").strip()
        except Exception:
            embedded = ""
        if len(embedded) >= min_chars:
            page_texts.append(embedded)
        else:
            scanned_pages.append(index)
            page_texts.append(embedded)  # keep whatever little text exists

    result = ExtractionResult(
        text="",
        page_count=len(reader.pages),
        is_image_based=bool(scanned_pages),
    )

    if scanned_pages and ocr_enabled:
        _resolve_tesseract(config)
        ocr_texts, images = _ocr_pages(pdf_bytes, scanned_pages, config, want_images)
        for page_no, ocr_text in ocr_texts.items():
            base = page_texts[page_no - 1]
            if ocr_text and base:
                page_texts[page_no - 1] = f"{base}\n{ocr_text}"
            elif ocr_text:
                page_texts[page_no - 1] = ocr_text
        result.ocr_page_numbers = sorted(ocr_texts)
        result.page_images = images
    elif scanned_pages and not ocr_enabled:
        joined = "\n\n".join(t for t in page_texts if t).strip()
        if len(joined) < min_chars and (config is None or config.strict_gate):
            raise OCRUnavailableError(
                "PDF appears image-based but OCR is disabled and no text layer exists"
            )

    result.text = "\n\n".join(t for t in page_texts if t).strip()
    return result


def _ocr_pages(
    pdf_bytes: bytes,
    pages: list[int],
    config: "SanitizerConfig | None",
    want_images: bool,
) -> tuple[dict[int, str], list[object]]:
    """OCR the given 1-indexed pages. Returns ``{page_no: text}`` and images."""
    try:
        import fitz  # PyMuPDF
        import pytesseract
        from PIL import Image
    except Exception as exc:
        if config is None or config.strict_gate:
            raise OCRUnavailableError(
                "scanned PDF needs OCR but pymupdf/pytesseract/Pillow are not installed"
            ) from exc
        _log.warning("OCR deps missing (%s); scanned pages will be blank.", type(exc).__name__)
        return {}, []

    scale = config.ocr_dpi_scale if config else 2.0
    language = config.ocr_language if config else "eng"
    wanted = set(pages)
    texts: dict[int, str] = {}
    images: list[object] = []
    document = None
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
        for index, page in enumerate(document, start=1):
            if index not in wanted:
                continue
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            try:
                texts[index] = pytesseract.image_to_string(
                    image,
                    lang=language,
                    config="--oem 3 --psm 6 -c preserve_interword_spaces=1",
                ).strip()
            except Exception as exc:
                _log.warning("OCR failed on page %d: %s", index, type(exc).__name__)
                texts[index] = ""
            if want_images:
                images.append(image)
    except Exception as exc:
        raise ExtractionError(f"OCR rendering failed: {exc}") from exc
    finally:
        if document is not None:
            document.close()
    return texts, images

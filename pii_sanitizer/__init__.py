"""pii_sanitizer — sanitize documents before they reach an LLM, restore after.

Quick start
-----------
>>> from pii_sanitizer import sanitize_pdf, restore
>>> result = sanitize_pdf(pdf_bytes)          # local: extract, OCR, redact
>>> llm_response = call_gemini(result.sanitized_text)  # only placeholders leave
>>> final = restore(llm_response, result.vault)         # originals back, locally
>>> result.vault.close()                       # zeroize the mapping when done

The only value that ever leaves the machine is ``result.sanitized_text``. The
reverse mapping lives in ``result.vault`` and is never serialized to the network.

For a drop-in replacement of the project's existing ``privacy_filter`` calls,
see :mod:`pii_sanitizer.integration`.
"""

from __future__ import annotations

from .config import SanitizerConfig, load_config
from .errors import (
    ConfigError,
    ExtractionError,
    LeakDetectedError,
    OCRUnavailableError,
    SanitizerError,
    VaultError,
)
from .gate import find_leaks, is_cloud_safe, require_cloud_safe
from .logging_utils import configure_logging
from .sanitizer import (
    SanitizationResult,
    restore,
    sanitize_pdf,
    sanitize_text,
)
from .spans import Span
from .vault import Vault

__version__ = "1.0.0"

__all__ = [
    "sanitize_pdf",
    "sanitize_text",
    "restore",
    "SanitizationResult",
    "Vault",
    "Span",
    "SanitizerConfig",
    "load_config",
    "configure_logging",
    "find_leaks",
    "is_cloud_safe",
    "require_cloud_safe",
    "SanitizerError",
    "ExtractionError",
    "OCRUnavailableError",
    "LeakDetectedError",
    "VaultError",
    "ConfigError",
    "__version__",
]

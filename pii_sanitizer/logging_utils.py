"""Logging that cannot leak PII.

Even with a perfect sanitizer, a careless ``log.info("processing %s", raw_text)``
would defeat the whole design. :class:`RedactingFilter` is installed on the
package logger so that *every* record — message and args — is scrubbed of
PII-shaped tokens before it reaches any handler, including debug logs.

This is defense-in-depth: application code should still avoid logging raw
document text, but if it slips through, the filter neutralizes it.
"""

from __future__ import annotations

import logging
import re

# Coarse, aggressive scrubbers. Precision matters less here than never leaking:
# it is fine to over-redact a log line.
_SCRUBBERS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?<!\d)\d{3}[-\s]\d{2}[-\s]\d{4}(?!\d)"), "[SSN]"),
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[EMAIL]"),
    (re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)"), "[PHONE]"),
    (re.compile(r"(?<!\d)\d{2}-\d{7}(?!\d)"), "[TAXID]"),
    (re.compile(r"(?<!\d)\d{6,}(?!\d)"), "[NUM]"),  # long digit runs (accounts, etc.)
]


def scrub(text: str) -> str:
    out = str(text)
    for pattern, repl in _SCRUBBERS:
        out = pattern.sub(repl, out)
    return out


class RedactingFilter(logging.Filter):
    """A logging filter that scrubs PII from the record message and its args."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003 - stdlib name
        try:
            if isinstance(record.msg, str):
                record.msg = scrub(record.msg)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {k: _scrub_arg(v) for k, v in record.args.items()}
                else:
                    record.args = tuple(_scrub_arg(a) for a in record.args)
        except Exception:
            # A logging filter must never raise; fail open to a scrubbed default.
            record.msg = "[log record suppressed by RedactingFilter]"
            record.args = None
        return True


def _scrub_arg(value: object) -> object:
    return scrub(value) if isinstance(value, str) else value


def configure_logging(level: str = "INFO", *, redact: bool = True) -> logging.Logger:
    """Configure and return the package logger with the redaction filter attached."""
    logger = logging.getLogger("pii_sanitizer")
    logger.setLevel(getattr(logging, str(level).upper(), logging.INFO))
    if redact and not any(isinstance(f, RedactingFilter) for f in logger.filters):
        logger.addFilter(RedactingFilter())
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        if redact:
            handler.addFilter(RedactingFilter())
        logger.addHandler(handler)
    logger.propagate = False
    return logger

"""Translation for the Spanish Reply tool: redact first, then use the caller's own Gemini key.

The current app sends the raw email text to Google Translate through the ``googletrans`` package,
with no redaction. That breaks RULES.md section 1, so the API does it this way instead:

1. ``pii_sanitizer.integration.redact_for_cloud_resilient`` (the same redactor the scanner uses)
   replaces names, SSNs, phone numbers, emails, account numbers, dates of birth and income with
   placeholders. If anything sensitive still remains, or names cannot be detected on this server,
   the text is refused, not sent.
2. Only the redacted text goes to Gemini, with the caller's own key (never a server key).
3. The placeholders in the answer are swapped back locally from the map that never left the
   server, so the user sees the real names and numbers in the translation.
"""
from __future__ import annotations

from functools import lru_cache

import cloud_client
from pii_sanitizer.config import load_config
from pii_sanitizer.integration import redact_for_cloud_resilient

from ..context import RequestContext
from ..errors import ApiError


@lru_cache(maxsize=4)
def _name_model_loads(model: str) -> bool:
    try:
        import spacy
        spacy.load(model)
        return True
    except Exception:
        return False


def name_detection_available() -> bool:
    """True when names written inside sentences can be found (the NER model loads).

    Without it the sanitizer only catches labelled names ("Borrower: ..."), which is fine for
    scanned forms but not for free-text emails. PII_NER_MODEL must be set on the server.
    """
    return _name_model_loads(load_config().ner_model)

SYSTEM = (
    "You are a professional translator for a mortgage processor. Translate the user's text "
    "faithfully and politely. Keep every bracketed token such as [PERSON_1], [EMAIL_2] or "
    "[AMOUNT_1] exactly as written. Output only the translation, with no notes."
)


def translate(ctx: RequestContext, text: str, target: str) -> str:
    """Translate ``text`` into ``target`` ("English" or "Spanish")."""
    if ctx.sandbox or not ctx.gemini_key:
        raise ApiError(400, "ai_key_needed", "Add your Gemini API key in AI Settings to translate.")
    if not name_detection_available():
        raise ApiError(
            503, "redaction_unavailable",
            "Translation is switched off because names cannot be detected safely on this server.",
        )
    sanitized, replacements, _forced, remaining = redact_for_cloud_resilient(text)
    if remaining:
        raise ApiError(
            400, "cannot_redact",
            "This text has personal details that could not be removed safely, so it was not sent. "
            "Translate it manually.",
        )
    if not sanitized.strip():
        raise ApiError(400, "nothing_to_translate", "There is nothing to translate.")
    prompt = f"Translate this text into {target}:\n\n{sanitized}"
    try:
        answer = cloud_client._generate(
            prompt, SYSTEM, "gemini", ctx.gemini_key, cloud_client.DEFAULT_MODELS["gemini"], timeout=60,
        )
    except Exception:
        raise ApiError(502, "translation_failed", "The translation did not finish. Try again in a minute.")
    answer = str(answer or "").strip()
    if not answer:
        raise ApiError(502, "translation_failed", "The translation came back empty. Try again.")
    for placeholder, original in replacements.items():
        answer = answer.replace(placeholder, original)
    return answer

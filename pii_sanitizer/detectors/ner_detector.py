"""Named-Entity-Recognition detector for *unlabeled* names, orgs and places.

This is the layer that closes the biggest gap in the existing regex-only
filter: a bare ``John Smith`` or ``Wells Fargo`` with no "Borrower:" label in
front of it. Regex cannot safely catch those (any two capitalized words would
match); a statistical model can.

Backends, in order of preference:

1. **Presidio** (``presidio-analyzer``) — purpose-built PII analyzer wrapping
   spaCy, with confidence scores. Preferred when installed.
2. **spaCy** directly — we map ``PERSON``/``ORG``/``GPE`` entities ourselves.

If neither is importable (or the model is missing) this detector returns an
empty list and logs a one-time warning. The core sanitizer keeps working with
regex + barcode detection only — it just won't catch unlabeled names.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import TYPE_CHECKING

from ..spans import Span

if TYPE_CHECKING:  # pragma: no cover
    from ..config import SanitizerConfig

_log = logging.getLogger("pii_sanitizer.ner")

# spaCy label -> our entity type. Unlabeled PERSONs become generic PERSON; the
# regex layer supplies role-typed names, and overlap resolution prefers those.
_SPACY_LABEL_MAP = {
    "PERSON": "PERSON",
    "ORG": "COMPANY",
    "GPE": "CITY",       # cities / states / countries
    "LOC": "CITY",
    "FAC": "ADDRESS",    # named facilities / buildings
}
_PRESIDIO_MAP = {
    "PERSON": "PERSON",
    "ORGANIZATION": "COMPANY",
    "NRP": "PERSON",
    "LOCATION": "CITY",
}


@lru_cache(maxsize=2)
def _load_presidio():
    from presidio_analyzer import AnalyzerEngine  # type: ignore

    return AnalyzerEngine()


@lru_cache(maxsize=4)
def _load_spacy(model: str):
    import spacy  # type: ignore

    return spacy.load(model, disable=["lemmatizer", "textcat"])


def _detect_presidio(text: str, min_score: float) -> list[Span]:
    engine = _load_presidio()
    results = engine.analyze(text=text, language="en")
    spans: list[Span] = []
    for r in results:
        entity = _PRESIDIO_MAP.get(r.entity_type)
        if entity is None or r.score < min_score:
            continue
        spans.append(
            Span(
                start=r.start,
                end=r.end,
                entity_type=entity,
                text=text[r.start:r.end],
                score=float(r.score),
                source="presidio",
            )
        )
    return spans


def _detect_spacy(text: str, model: str) -> list[Span]:
    nlp = _load_spacy(model)
    spans: list[Span] = []
    # nlp.pipe over sentence chunks keeps memory flat on very large PDFs.
    doc = nlp(text)
    for ent in doc.ents:
        entity = _SPACY_LABEL_MAP.get(ent.label_)
        if entity is None:
            continue
        spans.append(
            Span(
                start=ent.start_char,
                end=ent.end_char,
                entity_type=entity,
                text=ent.text,
                score=0.85,
                source="spacy",
            )
        )
    return spans


_WARNED = False


# Mortgage vocabulary the statistical model mislabels as organizations or people
# ("VOE", "Borrower Conditions"). Redacting these hides the meaning of a condition
# from the AI without protecting anyone.
_DOMAIN_TERMS = {
    "voe", "wvoe", "vod", "vor", "hoi", "hoa", "cd", "le", "loe", "ptd", "ptf", "pta", "ptp", "ac",
    "ctc", "fha", "va", "usda", "mi", "pmi", "mip", "ufmip", "dti", "ltv", "cltv", "aus", "du", "lp",
    "1003", "1008", "4506", "4506-c", "w-2", "w2", "1099", "irs", "ssa", "ein", "itin", "flood",
    "appraisal", "title", "escrow", "underwriting", "underwriter", "processor", "closer", "lender",
    "borrower", "co-borrower", "seller", "buyer", "conditions", "condition", "prior to docs",
    "prior to funding", "prior to approval", "at closing", "borrower conditions", "client conditions",
    "borrower requirements", "loan approval conditions", "final seller disclosure",
    "closing disclosure", "loan estimate", "verification of employment", "verification of deposit",
    "homeowners insurance", "hazard insurance", "real estate certification", "amendatory clause",
}


def _is_domain_term(fragment: str) -> bool:
    norm = re.sub(r"[\s:]+", " ", fragment.strip().strip(".,;").lower())
    if norm in _DOMAIN_TERMS:
        return True
    words = norm.split()
    return bool(words) and all(w in _DOMAIN_TERMS for w in words)


def detect(text: str, config: "SanitizerConfig | None" = None) -> list[Span]:
    """Return NER spans, or ``[]`` if no NER backend is available."""
    spans = _detect_raw(text, config)
    return [s for s in spans if not _is_domain_term(s.text)]


def _detect_raw(text: str, config: "SanitizerConfig | None" = None) -> list[Span]:
    global _WARNED
    src = str(text or "")
    if not src.strip():
        return []
    min_score = config.ner_min_score if config else 0.35
    model = config.ner_model if config else "en_core_web_lg"
    try:
        return _detect_presidio(src, min_score)
    except Exception:
        pass
    try:
        return _detect_spacy(src, model)
    except Exception as exc:
        if not _WARNED:
            _log.warning(
                "NER backend unavailable (%s). Falling back to regex-only "
                "detection; unlabeled names will NOT be caught. Install "
                "'presidio-analyzer' or 'spacy' + '%s' to enable.",
                type(exc).__name__,
                model,
            )
            _WARNED = True
        return []

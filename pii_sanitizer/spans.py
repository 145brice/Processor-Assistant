"""Entity span model and overlap resolution.

A :class:`Span` is the common currency between every detector (regex, NER,
barcode) and the sanitizer orchestrator. Detectors only need to emit spans;
they never touch the text directly. This keeps detectors independent and makes
overlap handling a single, well-tested concern.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True, slots=True)
class Span:
    """A detected sensitive region of text.

    Attributes:
        start: Inclusive start offset into the source text.
        end: Exclusive end offset into the source text.
        entity_type: Canonical entity label, e.g. ``"BORROWER"`` or ``"SSN"``.
            Must be one of the roles the :class:`~pii_sanitizer.vault.Vault`
            understands; unknown types fall back to ``"PERSON"``/``"OTHER"``.
        text: The exact matched substring (``source[start:end]``).
        score: Detector confidence in ``[0.0, 1.0]``. Used for tie-breaking.
        source: Name of the detector that produced the span (diagnostics only).
    """

    start: int
    end: int
    entity_type: str
    text: str
    score: float = 1.0
    source: str = "unknown"

    def __post_init__(self) -> None:
        if self.start < 0 or self.end < self.start:
            raise ValueError(f"invalid span offsets: start={self.start} end={self.end}")

    @property
    def length(self) -> int:
        return self.end - self.start

    def overlaps(self, other: "Span") -> bool:
        return self.start < other.end and other.start < self.end


# Priority controls which detector wins when two spans overlap. Higher wins.
# Structured, high-precision identifiers outrank fuzzy NER name guesses so that,
# e.g., an SSN embedded near a labeled name is never swallowed by a PERSON span.
_DEFAULT_PRIORITY: dict[str, int] = {
    "SSN": 100,
    "TAX_ID": 98,
    "ROUTING_NUMBER": 96,
    "ACCOUNT_NUMBER": 94,
    "BANK_ACCOUNT": 94,
    "LOAN_NUMBER": 92,
    "MORTGAGE_NUMBER": 92,
    "PASSPORT": 90,
    "DRIVERS_LICENSE": 90,
    "EMAIL": 88,
    "PHONE": 86,
    "DATE_OF_BIRTH": 84,
    "PROPERTY_IDENTIFIER": 80,
    "QR_CODE": 78,
    "BARCODE": 78,
    "SIGNATURE": 76,
    "ADDRESS": 70,
    "ZIP": 60,
    # Role-typed names (from labeled context) beat generic NER PERSON hits.
    "BORROWER": 55,
    "COBORROWER": 55,
    "SELLER": 55,
    "BUYER": 55,
    "REALTOR": 55,
    "LOAN_OFFICER": 55,
    "PROCESSOR": 55,
    "UNDERWRITER": 55,
    "LENDER": 52,
    "EMPLOYER": 52,
    "COMPANY": 50,
    "COUNTY": 45,
    "CITY": 44,
    "STATE": 30,
    "PERSON": 40,
    "OTHER": 10,
}


def priority_for(entity_type: str) -> int:
    return _DEFAULT_PRIORITY.get(entity_type.upper(), _DEFAULT_PRIORITY["OTHER"])


def resolve_overlaps(spans: Iterable[Span]) -> list[Span]:
    """Return a non-overlapping, position-sorted list of the strongest spans.

    When two spans overlap the winner is chosen by, in order:
    entity priority, then confidence score, then span length (longer wins),
    then earliest start. The loser is discarded entirely rather than truncated,
    which avoids emitting partial/corrupt placeholders.
    """

    ordered = sorted(
        spans,
        key=lambda s: (
            -priority_for(s.entity_type),
            -s.score,
            -s.length,
            s.start,
        ),
    )
    kept: list[Span] = []
    for span in ordered:
        if any(span.overlaps(k) for k in kept):
            continue
        kept.append(span)
    kept.sort(key=lambda s: s.start)
    return kept

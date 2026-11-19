"""Document type detection for POST /api/scan/detect (task T-20).

Same behaviour as the Streamlit scanner (show_dashboard in app.py):
1. ai_engine.detect_doc_type reads the first pages' text with local rules (no AI, nothing leaves
   the server).
2. If that finds nothing or only a weak match, the filename keywords below decide. They are
   copied from app.py `_FILENAME_FALLBACKS` (same order: first match wins).

Then the result is fitted to the API contract: types outside the contract's DocType list become
"Unknown" (Streamlit silently pre-selected "Approval Letter" for these), and the confidence
values "None" and "Filename" become "Low".
"""
from __future__ import annotations

from typing import get_args

import ai_engine

from .models import DocType

DOC_TYPES: frozenset[str] = frozenset(get_args(DocType))

# Copied from app.py show_dashboard `_FILENAME_FALLBACKS`. Order matters: first match wins.
FILENAME_FALLBACKS: list[tuple[list[str], str]] = [
    (["approval", "commitment letter", "du findings", "desktop underwriter",
      "lpa findings", "aus findings", "du ", "lpa ", "conditional approval",
      "loan approval", "underwriting approval", "uw approval",
      "loan decision", "underwriting decision", "uw decision",
      "credit decision", "decision", "findings", "loan estimate approval",
      "conditions list", "loan conditions"], "Approval Letter"),
    (["coe", "certificate of eligibility", "cert of eligib"], "VA Certificate of Eligibility"),
    (["dd214", "dd-214", "dd 214", "discharge", "dd_214"], "DD-214"),
    (["license", "drivers license", "id card", "government id", "photo id", "passport", "id -", "- id", "_id"], "Government ID"),
    (["w2", "w-2", "wage and tax"], "W-2"),
    (["1099"], "1099"),
    (["1003", "urla", "loan application"], "1003 Application"),
    (["credit report", "tri merge", "trimerge", "credit_report"], "Credit Report"),
    (["appraisal"], "Appraisal"),
    (["bank statement", "bank_statement"], "Bank Statement"),
    (["purchase contract", "purchase agreement", "sales contract"], "Purchase Contract"),
    (["title commitment", "title insurance"], "Title Commitment"),
    (["mortgage statement", "loan statement"], "Mortgage Statement"),
    (["paystub", "pay stub", "paycheck", "pay check", "earnings statement"], "Pay Stub"),
    (["tax return", "1040", "tax transcript"], "Tax Return"),
    (["hoi", "hazard insurance", "homeowner insurance", "home owner insurance",
      "insurance binder", "insurance policy", "hoi dec", "insurance dec page",
      "declarations page"], "Hazard Insurance"),
]


def filename_fallback(filename: str) -> str | None:
    """Doc type suggested by the filename alone, or None. Same rules as app.py."""
    lowered = filename.lower().replace("_", " ").replace("-", " ")
    for keywords, doc_type in FILENAME_FALLBACKS:
        if any(keyword in lowered for keyword in keywords):
            return doc_type
    return None


def detect(filename: str, pdf_bytes: bytes) -> dict:
    """Return {"detected_type", "confidence"} in the contract's terms."""
    try:
        found = ai_engine.detect_doc_type(pdf_bytes) or {}
    except Exception:
        found = {}
    doc_type = str(found.get("doc_type") or "Unknown")
    confidence = str(found.get("confidence") or "None")

    if doc_type == "Unknown" or confidence in ("None", "Low"):
        by_name = filename_fallback(filename)
        if by_name:
            doc_type, confidence = by_name, "Filename"

    if doc_type not in DOC_TYPES:
        doc_type = "Unknown"
    if confidence not in ("High", "Medium", "Low"):
        confidence = "Low"
    return {"detected_type": doc_type, "confidence": confidence}

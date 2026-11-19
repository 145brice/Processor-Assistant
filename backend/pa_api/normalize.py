"""Condition normalisation for scan results (task T-21).

`normalize_scanned_conditions` and its helpers are copied from app.py (Streamlit) so the API
behaves the same: `_normalize_scanned_conditions`, `_condition_override_parties`,
`_infer_condition_party`, `_PARTY_KEYWORDS_THIRD_PARTY`, `_PARTY_KEYWORDS_BORROWER_ACTION`
(routing version v20260526a). Keep them in step with app.py until the switch-over.

`to_contract_conditions` then fits the rows to API_CONTRACT.md `Condition`.
"""
from __future__ import annotations

import re
from typing import get_args

from .models import ConditionStatus

# Keyword routing for condition responsibility. Copied from app.py.
# Checked top to bottom. Earlier entries win.
_PARTY_KEYWORDS_THIRD_PARTY = [
    ("Borrower", [
        "proof of paid", "proof of pay", "paid by borrower",
        "borrower paid", "paid outside closing", " poc ", " poc.",
        "homebuyer education", "homebuyer class", "homebuyer course",
        "fannie mae class", "freddie mac class", "fnma class", "fhlmc class",
        "framework class", "counseling certificate", "education certificate",
        "course completion",
        "earnest money", "earnest deposit", " emd ", " emd.", " emd,",
        "good faith deposit", "emd receipt", "earnest money receipt",
        "letter of explanation", " loe ", " loe.", " loe,",
        "explanation letter", "explanation needed",
        "gift letter", "gift funds", "gift donor", "donor letter",
        "donor statement",
        "name affidavit", "aka affidavit", "signature affidavit",
    ]),
    ("Processor", [
        "copy of the appraisal invoice", "copy of the credit report invoice",
        "copy of the verification of employment invoice",
        "copy of the voe invoice", "copy of the invoice", "fee sheet",
        "broker to ", "broker has ", "fha case", "case number assignment",
        "case # transferred", "case transferred", "case query",
        "transferred to uwm", "sponsor id", "business tax id",
        "corp to obtain", "internal lock", "fha connection",
    ]),
    ("Appraiser", [
        "appraisal", "appraiser", "1004d", "1004 ", "1004-d",
        "property inspection", "property valuation", "final inspection",
        "ead portal", "appraisal logging", "appraisal condition",
        "successful submission report", "ssr",
    ]),
    ("Title", [
        "title commitment", "title search", "title review", "title insurance",
        "clear title", "title company", "settlement agent", "wiring instructions",
        "lien", "payoff statement", "payoff account", "estoppel", "survey",
        "alta", "cpl", "preliminary cd", "warranty deed", "deed of trust",
        "vesting", "security instrument", "title package", "closing disclosure",
        "final cd", "final closing disclosure", "initial closing disclosure",
        "initial cd", "cd delivery", "cd issued",
    ]),
    ("Insurance", [
        "hazard insurance", "homeowner insurance", "homeowner's insurance",
        "homeowners insurance", "hoi policy", "hoi binder", "insurance binder",
        "hazard dec page", "declarations page", "flood certification",
        "flood determination", "wind coverage", "mortgagee clause",
        "dwelling coverage", "replacement cost",
    ]),
    ("Closer", [
        "closer ", "closing package", "lock desk", "ctc", "clear to close",
        "fund release", "wire authorization", "closing agent", "closer to confirm",
        "closer to provide",
    ]),
    ("Underwriter", [
        "underwriting review", "underwriter approval", "underwriter review",
        "compliance review", "lender requirements", "investor guidelines",
        "lqi report", "loan quality initiative", "second-level review",
        "slr ", "qc review", "quality control",
        "pmi approval", "pmi coverage", " pmi ", "mi approval", "mi coverage",
        "max interest rate", "interest rate not to exceed", "rate lock",
        "max piti", "max ltv", "max dti", "max cltv",
    ]),
    ("Employer", [
        "verbal verification of employment", "written verification of employment",
        "voe ", "wvoe", "verbal voe", "written voe", "employer verification",
        "employment confirmation", "current voe", "employer to confirm",
    ]),
    ("Realtor", [
        "purchase contract", "purchase agreement", "sales agreement",
        "realtor", "listing agent", "selling agent", "buyer's agent",
        "seller's agent", "real estate agent", "real estate certification",
        "real estate cert", "fha amendatory clause", "amendatory clause",
        "arm's length affidavit", "required parties sign",
    ]),
    ("Seller", [
        "seller to provide", "seller's closing", "seller credit",
        "seller concession", "seller contribution", "seller signature",
    ]),
]

_PARTY_KEYWORDS_BORROWER_ACTION = [
    "missing signature", "sign document", "sign disclosure",
    "provide paystub", "provide pay stub", "provide bank statement",
    "provide tax return", "provide w-2", "provide w2", "missing w-2",
    "missing 1040", "provide 1040", "provide 1099", "provide ssa",
    "provide social security", "verify employment",
    "provide income verification", "provide asset", "provide gift letter",
    "borrower consent", "borrower authorization", "borrower acknowledgment",
    "provide id", "provide identification", "provide driver's license",
    "missing disclosure", "provide explanation letter", "letter of explanation",
    "debt verification needed", "income verification needed",
    "asset documentation needed", "motivation letter", "gift funds",
    "earnest money", "name affidavit", "aka",
]


def _condition_override_parties(desc: str):
    """Return forced party defaults for borrower-facing special cases."""
    text = str(desc or "").lower()
    if (
        "real estate certification" in text
        or "real estate cert" in text
        or "fha amendatory clause" in text
        or "amendatory clause" in text
    ):
        return ["Borrower", "Realtor", "Seller"]
    if (
        "invoice" in text
        and any(k in text for k in ["hoi", "homeowner", "homeowners", "hazard insurance", "insurance"])
    ):
        return ["Borrower"]
    if any(
        k in text
        for k in [
            "hoi",
            "homeowner insurance",
            "homeowner's insurance",
            "homeowners insurance",
            "hazard insurance",
        ]
    ):
        return ["Borrower"]
    if (
        "final selling disclosure" in text
        or "final seller disclosure" in text
        or "seller closing disclosure" in text
        or "seller's closing disclosure" in text
        or "final sales disclosure" in text
        or "seller cd" in text
        or ("closing disclosure" in text and any(k in text for k in ["seller", "sale of current", "current home", "departing residence", "departing home"]))
    ):
        return ["Borrower"]
    if (
        "closing disclosure" in text
        or "final cd" in text
        or "final closing disclosure" in text
        or "initial closing disclosure" in text
        or "initial cd" in text
        or "cd delivery" in text
        or "cd issued" in text
        or "preliminary cd" in text
        or "title package" in text
    ):
        return ["Title"]
    return None


def _infer_condition_party(desc: str) -> str:
    """Infer responsible party from condition text using layered keyword lists."""
    text = str(desc or "").lower()

    override_parties = _condition_override_parties(text)
    if override_parties:
        return override_parties[0]

    for party, keywords in _PARTY_KEYWORDS_THIRD_PARTY:
        if any(k in text for k in keywords):
            return party

    if any(k in text for k in _PARTY_KEYWORDS_BORROWER_ACTION):
        return "Borrower"

    return "Borrower"


def normalize_scanned_conditions(raw_conditions) -> list[dict]:
    """Convert extractor output into UI condition rows. Copied from app.py."""
    _placeholder_labels = {
        "AMOUNT": "the amount",
        "PERSON": "the named party",
        "EMAIL": "the email",
        "PHONE": "the phone number",
        "SSN": "the SSN",
        "ACCOUNT_NUMBER": "the account number",
        "DATE_OF_BIRTH": "the date of birth",
        "EXACT_DATE": "the date",
        "ADDRESS": "the property address",
        "KNOWN_VALUE": "the provided detail",
        "INCOME_AMOUNT": "the income amount",
        "PROPERTY_IDENTIFIER": "the property identifier",
    }

    def _neutralize_redaction_placeholders(value: str) -> str:
        def _label(match: re.Match) -> str:
            token = match.group(0)[1:-1]
            base = re.sub(r"_\d+$", "", token)
            return _placeholder_labels.get(base, _placeholder_labels.get(token, "the redacted detail"))
        return re.sub(r"\[[A-Z][A-Z0-9_]*\]", _label, str(value or ""))

    def _clean_desc(value: str) -> str:
        text = _neutralize_redaction_placeholders(value)
        text = " ".join(str(text or "").split()).strip(" -*\t")
        text = re.sub(r"(?i)\s*\b(?:Needed|Requested|Cleared|Waived)\s*$", "", text).strip()
        repeated = re.match(
            r"^([A-Z0-9-]{5,})\s+(.{5,90}?)\s*-\s*\1\s+\2\b(.*)$",
            text,
            flags=re.I,
        )
        if repeated:
            text = f"{repeated.group(2)}{repeated.group(3)}".strip()
        text = re.sub(r"^[A-Z0-9-]{5,}\s+(?=(?:Debts?|Payoff|Assets?|Income|Credit)\b)", "", text, flags=re.I)
        return re.sub(r"\s+", " ", text).strip(" -.;")

    def _is_extractor_chrome(value: str) -> bool:
        low = str(value or "").strip().lower()
        return (
            not low
            or low in {"condition", "responsible", "status", "-----------"}
            or "condition(s) extracted from document" in low
            or "each row above is actual text" in low
            or "select conditions below to draft emails" in low
            or low.startswith("| # | condition")
        )

    rows = []
    if isinstance(raw_conditions, list):
        source = raw_conditions
    elif isinstance(raw_conditions, str):
        if "No specific conditions found in this document" in raw_conditions:
            return []
        source = []
        for line in raw_conditions.splitlines():
            line = line.strip()
            if not line or line.startswith("**") or line.startswith("```"):
                continue
            if any(skip in line for skip in (
                "Possible reasons:",
                "Raw text preview",
                "PDF may be a scanned image",
                "Conditions may use non-standard formatting",
                "This document type may not contain conditions",
                "If you see condition text above",
            )):
                continue
            if line.startswith("|") and line.endswith("|"):
                parts = [p.strip() for p in line.strip("|").split("|")]
                if len(parts) >= 4 and parts[0] not in {"#", "---"} and not parts[0].startswith("-"):
                    source.append({
                        "num": parts[0],
                        "desc": parts[1],
                        "party": parts[2],
                        "status": parts[3],
                        "confidence": parts[4] if len(parts) >= 5 else "",
                    })
                continue
            cleaned = _clean_desc(line)
            if cleaned and not _is_extractor_chrome(cleaned) and "No specific conditions found" not in cleaned:
                source.append({"desc": cleaned})
    else:
        source = []

    for item in source:
        cond = dict(item) if isinstance(item, dict) else {"desc": str(item)}
        desc = _clean_desc(cond.get("desc") or cond.get("description") or "")
        if _is_extractor_chrome(desc):
            continue
        cond["num"] = str(len(rows) + 1)
        cond["desc"] = desc
        _override_parties = _condition_override_parties(desc)
        if _override_parties:
            cond["party"] = _override_parties[0]
            cond["parties"] = _override_parties
            cond["status"] = cond.get("status") or "Needed"
            rows.append(cond)
            continue
        _routed = _infer_condition_party(desc)
        _gem_party = (cond.get("party") or "").strip()
        if _routed != "Borrower":
            cond["party"] = _routed
        elif _gem_party and _gem_party != "Borrower":
            cond["party"] = _gem_party
        else:
            cond["party"] = "Borrower"
        cond["status"] = cond.get("status") or "Needed"
        rows.append(cond)
    return rows


_STATUSES = {s.lower(): s for s in get_args(ConditionStatus)}


def to_contract_conditions(rows: list[dict]) -> list[dict]:
    """Fit normalised rows to the contract's Condition: int num, known status, optional section."""
    out = []
    for index, row in enumerate(rows, start=1):
        status = _STATUSES.get(str(row.get("status") or "").strip().lower(), "Needed")
        section = str(row.get("section") or "").strip() or None
        out.append({
            "num": index,
            "desc": str(row.get("desc") or ""),
            "party": str(row.get("party") or "Borrower"),
            "status": status,
            "section": section,
        })
    return out

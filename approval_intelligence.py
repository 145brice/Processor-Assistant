"""De-identified lender accuracy and condition-ownership intelligence.

This module is deliberately UI/storage agnostic.  Its persisted state contains
only lender-level aggregate counts and allowlisted language-pattern features.
Raw documents, condition sentences, filenames, loan identifiers, and borrower
data are never accepted by the persistence functions.
"""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy


OWNERS = ("Borrower", "Lender", "Broker / Loan Officer")

_LENDERS = (
    "United Wholesale Mortgage", "UWM", "Rocket Mortgage", "PennyMac",
    "Newrez", "loanDepot", "Freedom Mortgage", "Caliber Home Loans",
    "AmeriHome Mortgage", "Plaza Home Mortgage", "Flagstar Bank",
    "Guild Mortgage", "CrossCountry Mortgage", "Cardinal Financial",
    "Orion Lending", "American Financial Network", "AFN",
)

# Only these non-identifying semantic features may enter learned-pattern state.
_FEATURES = {
    "provide", "submit", "send", "upload", "sign", "explain", "paystub",
    "paystubs", "statement", "statements", "insurance", "identification",
    "funds", "gift", "letter", "tax", "returns", "verification", "verify",
    "employment", "income", "asset", "credit", "appraisal", "title",
    "underwriting", "underwriter", "lender", "funding", "compliance",
    "broker", "company", "license", "licensing", "standing", "corporate",
    "processor", "officer", "borrower", "employer", "obtain", "review",
    "confirm", "validate", "order", "transcript", "voe", "wvoe", "4506c",
}

_BORROWER_SIGNALS = {
    "borrower", "provide", "submit", "send", "upload", "sign", "explain",
    "paystub", "paystubs", "statement", "statements", "insurance",
    "identification", "funds", "gift", "letter", "returns",
}
_LENDER_SIGNALS = {
    "lender", "underwriting", "underwriter", "funding", "verification",
    "verify", "voe", "wvoe", "4506c", "order", "review", "validate",
    "confirm", "appraisal", "transcript",
}
_BROKER_SIGNALS = {
    "broker", "company", "license", "licensing", "standing", "corporate",
    "processor", "officer", "compliance",
}


def empty_state() -> dict:
    return {"version": 1, "lenders": {}, "ownership_patterns": {}}


def normalize_state(value) -> dict:
    if not isinstance(value, dict):
        return empty_state()
    out = empty_state()
    if isinstance(value.get("lenders"), dict):
        for lender, stats in value["lenders"].items():
            if not isinstance(stats, dict) or not clean_lender_name(lender):
                continue
            out["lenders"][clean_lender_name(lender)] = {
                "scans": max(0, int(stats.get("scans", 0) or 0)),
                "estimated_points": max(0, int(stats.get("estimated_points", 0) or 0)),
                "estimated_total": max(0, int(stats.get("estimated_total", 0) or 0)),
                "confirmed_correct": max(0, int(stats.get("confirmed_correct", 0) or 0)),
                "confirmed_total": max(0, int(stats.get("confirmed_total", 0) or 0)),
            }
    if isinstance(value.get("ownership_patterns"), dict):
        for signature, row in value["ownership_patterns"].items():
            if not re.fullmatch(r"[0-9a-f]{16}", str(signature)) or not isinstance(row, dict):
                continue
            owner = str(row.get("owner", ""))
            features = [f for f in row.get("features", []) if f in _FEATURES]
            if owner in OWNERS and features:
                out["ownership_patterns"][signature] = {
                    "owner": owner,
                    "features": sorted(set(features)),
                    "confirmations": max(1, int(row.get("confirmations", 1) or 1)),
                }
    return out


def clean_lender_name(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip(" |:-")
    if not text or len(text) > 80 or re.search(r"\d{4,}|@|\b(?:borrower|applicant)\b", text, re.I):
        return ""
    return text


def detect_lender_name(text: str) -> str:
    """Return only a lender company name; no surrounding document content."""
    head = "\n".join(str(text or "").splitlines()[:80])
    for lender in _LENDERS:
        if re.search(rf"\b{re.escape(lender)}\b", head, re.I):
            return lender
    for line in head.splitlines():
        cleaned = clean_lender_name(re.sub(r"(?i)^\s*(?:lender|creditor)\s*[:#-]?\s*", "", line))
        if cleaned and re.search(r"\b(?:mortgage|bank|credit union|home loans?|lending|financial)\b", cleaned, re.I):
            return cleaned
    return "Unknown Lender"


def pattern_features(condition: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", str(condition or "").lower())
    return sorted({token for token in tokens if token in _FEATURES})


def pattern_signature(features: list[str]) -> str:
    safe = sorted({f for f in features if f in _FEATURES})
    return hashlib.sha256("|".join(safe).encode("utf-8")).hexdigest()[:16] if safe else ""


def classify_condition(condition: str, state=None) -> dict:
    features = pattern_features(condition)
    signature = pattern_signature(features)
    learned = normalize_state(state).get("ownership_patterns", {}).get(signature)
    if learned:
        return {
            "owner": learned["owner"], "confidence": 0.99,
            "needs_confirmation": False, "pattern_signature": signature,
            "pattern_features": features, "source": "processor-confirmed pattern",
        }

    scores = {
        "Borrower": len(set(features) & _BORROWER_SIGNALS),
        "Lender": len(set(features) & _LENDER_SIGNALS),
        "Broker / Loan Officer": len(set(features) & _BROKER_SIGNALS),
    }
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    owner, top = ordered[0]
    second = ordered[1][1]
    # Require two coherent signals and clear separation for silent routing.
    confident = top >= 2 and top >= second + 2
    confidence = 0.92 if confident else (0.65 if top else 0.34)
    return {
        "owner": owner if top else "Borrower",
        "confidence": confidence,
        "needs_confirmation": not confident,
        "pattern_signature": signature,
        "pattern_features": features,
        "source": "de-identified language pattern",
    }


def apply_ownership(conditions: list[dict], state=None) -> list[dict]:
    out = []
    for condition in conditions or []:
        row = dict(condition)
        result = classify_condition(row.get("desc") or row.get("description") or "", state)
        row["ownership_bucket"] = result["owner"]
        row["ownership_confidence"] = result["confidence"]
        row["ownership_needs_confirmation"] = result["needs_confirmation"]
        row["ownership_pattern_signature"] = result["pattern_signature"]
        row["ownership_pattern_features"] = result["pattern_features"]
        out.append(row)
    return out


def record_scan(state, lender: str, conditions: list[dict], *, extraction_succeeded: bool = True) -> tuple[dict, dict]:
    out = normalize_state(deepcopy(state))
    lender = clean_lender_name(lender) or "Unknown Lender"
    stats = out["lenders"].setdefault(lender, {
        "scans": 0, "estimated_points": 0, "estimated_total": 0,
        "confirmed_correct": 0, "confirmed_total": 0,
    })
    rows = list(conditions or [])
    high = sum(1 for row in rows if not row.get("ownership_needs_confirmation"))
    # Each condition contributes one estimate; a successful but empty extraction
    # contributes one failed estimate so empty parses cannot appear 100% accurate.
    total = len(rows) or 1
    points = high if rows and extraction_succeeded else 0
    stats["scans"] += 1
    stats["estimated_points"] += points
    stats["estimated_total"] += total
    return out, lender_summary(out, lender)


def record_confirmation(state, lender: str, features: list[str], predicted: str, corrected: str) -> tuple[dict, dict]:
    if corrected not in OWNERS:
        raise ValueError("Unknown ownership bucket")
    out = normalize_state(deepcopy(state))
    lender = clean_lender_name(lender) or "Unknown Lender"
    stats = out["lenders"].setdefault(lender, {
        "scans": 0, "estimated_points": 0, "estimated_total": 0,
        "confirmed_correct": 0, "confirmed_total": 0,
    })
    stats["confirmed_total"] += 1
    if predicted == corrected:
        stats["confirmed_correct"] += 1
    safe_features = sorted({f for f in features if f in _FEATURES})
    signature = pattern_signature(safe_features)
    if signature:
        old = out["ownership_patterns"].get(signature, {})
        out["ownership_patterns"][signature] = {
            "owner": corrected,
            "features": safe_features,
            "confirmations": int(old.get("confirmations", 0) or 0) + 1,
        }
    return out, lender_summary(out, lender)


def lender_summary(state, lender: str) -> dict:
    lender = clean_lender_name(lender) or "Unknown Lender"
    stats = normalize_state(state)["lenders"].get(lender, {})
    confirmed_total = int(stats.get("confirmed_total", 0) or 0)
    if confirmed_total:
        percent = round(100 * int(stats.get("confirmed_correct", 0) or 0) / confirmed_total)
        basis = "processor-confirmed"
    else:
        total = int(stats.get("estimated_total", 0) or 0)
        percent = round(100 * int(stats.get("estimated_points", 0) or 0) / total) if total else None
        basis = "estimated"
    return {
        "lender": lender,
        "accuracy_percent": percent,
        "basis": basis,
        "scans": int(stats.get("scans", 0) or 0),
        "confirmed_total": confirmed_total,
    }

"""Owner-private, de-identified lender approval format learning."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy


_HEADINGS = (
    "approval conditions", "conditions", "prior to approval", "prior to documents",
    "prior to closing", "prior to funding", "prior to purchase", "at closing",
    "post closing", "underwriting decision", "loan summary", "property information",
    "borrower conditions", "lender conditions", "broker conditions",
)
_COLUMNS = (
    "condition number", "condition", "description", "status", "category", "owner",
    "responsible party", "date added", "date cleared", "notes", "reviewed by",
)
_GROUP_CODES = ("pta", "ptd", "ptc", "ptf", "ptp")


class LenderLearningError(ValueError):
    """Learning failure carrying only a safe, locally detected lender name."""

    def __init__(self, message: str, lender: str = "") -> None:
        super().__init__(message)
        self.lender = _safe_lender(lender) or "Unknown Lender"


def empty_state() -> dict:
    return {"version": 1, "lenders": {}}


def _safe_lender(value: str) -> str:
    from approval_intelligence import clean_lender_name

    lender = clean_lender_name(value)
    return lender if lender and lender != "Unknown Lender" else ""


def _small_int(value, maximum: int = 100000) -> int:
    try:
        return min(max(0, int(value or 0)), maximum)
    except (TypeError, ValueError):
        return 0


def normalize_state(value) -> dict:
    out = empty_state()
    if not isinstance(value, dict) or not isinstance(value.get("lenders"), dict):
        return out
    for key, row in value["lenders"].items():
        if not isinstance(row, dict):
            continue
        lender = _safe_lender(row.get("name", ""))
        if not lender or not re.fullmatch(r"[a-z0-9_-]{2,80}", str(key)):
            continue
        formats = {}
        for signature, fmt in (row.get("formats", {}) or {}).items():
            if not re.fullmatch(r"[0-9a-f]{16}", str(signature)) or not isinstance(fmt, dict):
                continue
            features = fmt.get("features", {})
            if not isinstance(features, dict):
                continue
            formats[str(signature)] = {
                "features": _normalize_features(features),
                "samples": max(1, _small_int(fmt.get("samples"), 100000)),
            }
        out["lenders"][str(key)] = {
            "name": lender,
            "total_samples": _small_int(row.get("total_samples"), 100000),
            "formats": formats,
        }
    return out


def _normalize_features(features: dict) -> dict:
    return {
        "page_count": _small_int(features.get("page_count"), 1000),
        "line_count_band": str(features.get("line_count_band", ""))[:20],
        "image_based": bool(features.get("image_based", False)),
        "numbering_styles": sorted({
            str(x) for x in features.get("numbering_styles", [])
            if str(x) in {"integer", "decimal", "parenthesized", "lettered", "bullet"}
        }),
        "headings": sorted({str(x) for x in features.get("headings", []) if str(x) in _HEADINGS}),
        "columns": sorted({str(x) for x in features.get("columns", []) if str(x) in _COLUMNS}),
        "group_codes": sorted({str(x) for x in features.get("group_codes", []) if str(x) in _GROUP_CODES}),
        "placeholder_categories": sorted({
            str(x).upper() for x in features.get("placeholder_categories", [])
            if re.fullmatch(r"[A-Z_]{2,40}", str(x).upper())
        }),
    }


def _feature_similarity(left: dict, right: dict) -> float:
    """Weighted structural similarity using only allowlisted profile fields."""
    a, b = _normalize_features(left), _normalize_features(right)
    score = 0.0
    weight = 0.0
    for key, field_weight in (
        ("headings", 4.0), ("columns", 3.0), ("group_codes", 3.0),
        ("numbering_styles", 2.0), ("placeholder_categories", 0.5),
    ):
        av, bv = set(a[key]), set(b[key])
        if av or bv:
            score += field_weight * (len(av & bv) / len(av | bv))
            weight += field_weight
    for key, field_weight in (("line_count_band", 1.5), ("image_based", 1.0)):
        score += field_weight if a[key] == b[key] else 0.0
        weight += field_weight
    if a["page_count"] and b["page_count"]:
        delta = abs(a["page_count"] - b["page_count"])
        score += 1.5 * max(0.0, 1.0 - (delta / max(a["page_count"], b["page_count"])))
        weight += 1.5
    return round(score / weight, 4) if weight else 0.0


def retrieve_profile_context(
    state,
    lender_name: str,
    document_text: str,
    *,
    page_count: int = 0,
    image_based: bool = False,
    limit: int = 3,
) -> dict:
    """Return safe lender-first parsing context with global similarity fallback."""
    normalized = normalize_state(state)
    lender = _safe_lender(lender_name)
    candidate = build_profile_from_sanitized(
        lender or "Document Candidate",
        document_text,
        page_count=page_count,
        image_based=image_based,
    )
    rows = []
    exact_rows = []
    for lender_row in normalized["lenders"].values():
        is_exact = bool(lender and lender_row["name"].casefold() == lender.casefold())
        for signature, fmt in lender_row["formats"].items():
            row = {
                "lender": lender_row["name"],
                "signature": signature,
                "similarity": _feature_similarity(candidate["features"], fmt["features"]),
                "samples": int(fmt.get("samples", 0) or 0),
                "features": _normalize_features(fmt["features"]),
            }
            rows.append(row)
            if is_exact:
                exact_rows.append(row)
    pool = exact_rows if exact_rows else rows
    pool.sort(key=lambda row: (row["similarity"], row["samples"]), reverse=True)
    matches = pool[:max(1, min(int(limit or 3), 5))]
    return {
        "detected_lender": lender or "Unknown Lender",
        "strategy": "detected_lender" if exact_rows else "structural_similarity",
        "matches": matches,
    }


def prompt_context(context: dict) -> str:
    """Serialize only normalized structural guidance for an AI parsing prompt."""
    safe = {
        "detected_lender": _safe_lender(context.get("detected_lender", "")) or "Unknown Lender",
        "strategy": (
            "detected_lender" if context.get("strategy") == "detected_lender"
            else "structural_similarity"
        ),
        "matches": [],
    }
    for row in list(context.get("matches", []))[:5]:
        lender = _safe_lender(row.get("lender", ""))
        signature = str(row.get("signature", ""))
        if not lender or not re.fullmatch(r"[0-9a-f]{16}", signature):
            continue
        safe["matches"].append({
            "lender": lender,
            "signature": signature,
            "similarity": max(0.0, min(float(row.get("similarity", 0) or 0), 1.0)),
            "samples": _small_int(row.get("samples"), 100000),
            "features": _normalize_features(row.get("features", {})),
        })
    return json.dumps(safe, sort_keys=True, separators=(",", ":"))


def record_parsed_observation(
    state,
    lender_name: str,
    document_text: str,
    parsed_conditions,
    *,
    page_count: int = 0,
    image_based: bool = False,
) -> tuple[dict, dict]:
    """Merge newly observed structure after parsing; never retain source wording."""
    if isinstance(parsed_conditions, list):
        parsed_text = "\n".join(
            str(row.get("desc") or row.get("description") or "")
            for row in parsed_conditions if isinstance(row, dict)
        )
    else:
        parsed_text = str(parsed_conditions or "")
    profile = build_profile_from_sanitized(
        lender_name,
        f"{document_text}\n{parsed_text}",
        page_count=page_count,
        image_based=image_based,
    )
    return record_profile(state, profile), profile


def build_profile_from_sanitized(
    lender_name: str,
    sanitized_text: str,
    *,
    page_count: int,
    image_based: bool,
) -> dict:
    """Reduce sanitized text to an allowlisted structural fingerprint."""
    lender = _safe_lender(lender_name)
    if not lender:
        raise ValueError("Lender could not be identified safely.")
    text = str(sanitized_text or "")
    lowered = text.lower()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    line_count = len(lines)
    if line_count < 30:
        line_band = "under_30"
    elif line_count < 75:
        line_band = "30_74"
    elif line_count < 150:
        line_band = "75_149"
    else:
        line_band = "150_plus"

    styles = set()
    for line in lines:
        if re.match(r"^\d+\.\d+\s", line):
            styles.add("decimal")
        elif re.match(r"^\d+[.)]\s", line):
            styles.add("integer")
        elif re.match(r"^\(\d+\)\s", line):
            styles.add("parenthesized")
        elif re.match(r"^[A-Z][.)]\s", line, re.I):
            styles.add("lettered")
        elif re.match(r"^[-*•]\s", line):
            styles.add("bullet")

    features = _normalize_features({
        "page_count": page_count,
        "line_count_band": line_band,
        "image_based": image_based,
        "numbering_styles": styles,
        "headings": [heading for heading in _HEADINGS if heading in lowered],
        "columns": [column for column in _COLUMNS if re.search(rf"\b{re.escape(column)}\b", lowered)],
        "group_codes": [code for code in _GROUP_CODES if re.search(rf"\b{code}\b", lowered)],
        "placeholder_categories": re.findall(r"\[([A-Z_]+)_\d+\]", text),
    })
    canonical = json.dumps(features, sort_keys=True, separators=(",", ":"))
    signature = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return {"lender": lender, "signature": signature, "features": features}


def learn_from_pdf(pdf_bytes: bytes) -> dict:
    """Sanitize locally, fail closed, and return no source text or PDF bytes."""
    from approval_intelligence import detect_lender_name
    from pii_sanitizer import SanitizerConfig, sanitize_pdf
    from pii_sanitizer.errors import SanitizerError
    from pii_sanitizer.extraction import extract

    config = SanitizerConfig(strict_gate=True, redact_money=True)
    lender = ""
    try:
        # Local-only first pass lets failures be attributed without retaining
        # or transmitting the PDF or its extracted text.
        local_extraction = extract(pdf_bytes, config)
        lender = detect_lender_name(local_extraction.text or "")
        result = sanitize_pdf(pdf_bytes, config=config)
        if result.residual_leaks:
            raise LenderLearningError(
                "Residual sensitive-data categories remain after sanitization.", lender
            )
        extraction = result.extraction
        profile = build_profile_from_sanitized(
            lender,
            result.sanitized_text,
            page_count=extraction.page_count if extraction else 0,
            image_based=bool(extraction and extraction.is_image_based),
        )
    except LenderLearningError:
        raise
    except (SanitizerError, ValueError) as exc:
        raise LenderLearningError(str(exc) or type(exc).__name__, lender) from exc
    profile["redacted_entities"] = {
        str(key): _small_int(count, 100000)
        for key, count in result.entity_counts.items()
        if re.fullmatch(r"[A-Z_]{2,40}", str(key))
    }
    return profile


def record_profile(state, profile: dict) -> dict:
    out = normalize_state(deepcopy(state))
    lender = _safe_lender(profile.get("lender", ""))
    signature = str(profile.get("signature", ""))
    if not lender or not re.fullmatch(r"[0-9a-f]{16}", signature):
        raise ValueError("Invalid de-identified lender profile.")
    key = re.sub(r"[^a-z0-9]+", "_", lender.lower()).strip("_")[:80]
    row = out["lenders"].setdefault(key, {"name": lender, "total_samples": 0, "formats": {}})
    fmt = row["formats"].setdefault(signature, {
        "features": _normalize_features(profile.get("features", {})),
        "samples": 0,
    })
    fmt["samples"] += 1
    row["total_samples"] += 1
    return normalize_state(out)

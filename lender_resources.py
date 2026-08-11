"""Curated public lender resources for approval-scan results."""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache


CATALOG_PATH = os.path.join(os.path.dirname(__file__), "lender_resources", "catalog.json")


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, ValueError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def resources_for_lender(lender_name: str) -> dict:
    """Return a safe catalog entry for a detected lender, or an empty dict."""
    needle = _normalized(lender_name)
    if not needle or needle == "unknown lender":
        return {}
    for key, entry in load_catalog().items():
        if not isinstance(entry, dict):
            continue
        aliases = entry.get("aliases", []) or []
        candidates = [entry.get("name", ""), *aliases]
        for alias in candidates:
            normalized_alias = _normalized(alias)
            if normalized_alias and (
                needle == normalized_alias
                or normalized_alias in needle
                or needle in normalized_alias
            ):
                resources = [
                    row for row in (entry.get("resources", []) or [])
                    if isinstance(row, dict)
                    and str(row.get("url", "")).startswith("https://")
                ]
                return {
                    "key": key,
                    "name": str(entry.get("name") or lender_name),
                    "resources": resources,
                }
    return {}

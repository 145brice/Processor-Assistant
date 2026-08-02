"""Typed configuration for the sanitizer, with file + environment overrides.

Precedence (lowest to highest): built-in defaults -> config file -> environment
variables. Environment variables are prefixed ``PII_`` (e.g. ``PII_ENABLE_NER``)
so the module can be tuned on Railway without editing files.

The config file may be YAML (if ``PyYAML`` is installed) or JSON; the loader
picks based on extension and falls back gracefully.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

from .errors import ConfigError

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return False
    return default


@dataclass(slots=True)
class SanitizerConfig:
    """All knobs for extraction, detection, gating and logging."""

    # -- extraction / OCR --
    ocr_enabled: bool = True
    ocr_dpi_scale: float = 2.0
    ocr_language: str = "eng"
    min_embedded_chars: int = 50  # below this a page is treated as image-based
    tesseract_cmd: str | None = None

    # -- detectors --
    enable_regex: bool = True
    enable_ner: bool = True
    enable_barcode: bool = True
    ner_model: str = "en_core_web_lg"
    ner_min_score: float = 0.35
    # Detect these categories. Names must match entity types in the detectors.
    enabled_entities: tuple[str, ...] = (
        "SSN", "TAX_ID", "ROUTING_NUMBER", "ACCOUNT_NUMBER", "LOAN_NUMBER",
        "PASSPORT", "DRIVERS_LICENSE", "EMAIL", "PHONE", "DATE_OF_BIRTH",
        "ADDRESS", "ZIP", "BORROWER", "COBORROWER", "SELLER", "BUYER",
        "REALTOR", "LOAN_OFFICER", "PROCESSOR", "UNDERWRITER", "LENDER",
        "EMPLOYER", "COMPANY", "PERSON", "COUNTY", "PROPERTY_IDENTIFIER",
        "QR_CODE", "BARCODE", "SIGNATURE",
    )

    # -- gate / safety --
    strict_gate: bool = True  # raise LeakDetectedError if residual PII remains
    redact_money: bool = False  # dollar amounts are usually needed by the LLM

    # -- logging --
    log_level: str = "INFO"
    redact_logs: bool = True  # scrub PII-shaped tokens from every log record

    # -- persistence --
    # If set, oversized vaults may spill to this dir as *encrypted* temp files.
    encrypted_spill_dir: str | None = None

    @classmethod
    def from_file(cls, path: str | os.PathLike[str]) -> "SanitizerConfig":
        p = Path(path)
        if not p.is_file():
            raise ConfigError(f"config file not found: {p}")
        raw = p.read_text(encoding="utf-8")
        try:
            if p.suffix.lower() in {".yaml", ".yml"}:
                data = _load_yaml(raw)
            else:
                data = json.loads(raw)
        except Exception as exc:
            raise ConfigError(f"could not parse config {p}: {exc}") from exc
        return cls.from_dict(data or {})

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SanitizerConfig":
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ConfigError(f"unknown config keys: {sorted(unknown)}")
        kwargs = dict(data)
        if "enabled_entities" in kwargs and isinstance(kwargs["enabled_entities"], list):
            kwargs["enabled_entities"] = tuple(kwargs["enabled_entities"])
        return cls(**kwargs)

    def with_env_overrides(self, environ: dict[str, str] | None = None) -> "SanitizerConfig":
        """Return a copy with ``PII_<UPPER_FIELD>`` env vars applied."""
        env = environ if environ is not None else dict(os.environ)
        updated: dict[str, Any] = {}
        for f in fields(self):
            key = f"PII_{f.name.upper()}"
            if key not in env:
                continue
            raw = env[key]
            current = getattr(self, f.name)
            if isinstance(current, bool):
                updated[f.name] = _as_bool(raw, current)
            elif isinstance(current, float):
                updated[f.name] = float(raw)
            elif isinstance(current, int):
                updated[f.name] = int(raw)
            elif isinstance(current, tuple):
                updated[f.name] = tuple(x.strip() for x in raw.split(",") if x.strip())
            else:
                updated[f.name] = raw
        if not updated:
            return self
        merged = {f.name: getattr(self, f.name) for f in fields(self)}
        merged.update(updated)
        return SanitizerConfig(**merged)


def _load_yaml(raw: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise ConfigError("PyYAML not installed; use a .json config instead") from exc
    return yaml.safe_load(raw)


def load_config(path: str | os.PathLike[str] | None = None) -> SanitizerConfig:
    """Load config from ``path`` (or ``PII_CONFIG_FILE`` env) then apply env overrides."""
    path = path or os.getenv("PII_CONFIG_FILE")
    base = SanitizerConfig.from_file(path) if path else SanitizerConfig()
    return base.with_env_overrides()

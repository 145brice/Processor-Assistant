"""Config precedence and span overlap resolution."""

from __future__ import annotations

import pytest

from pii_sanitizer.config import SanitizerConfig, load_config
from pii_sanitizer.errors import ConfigError
from pii_sanitizer.spans import Span, resolve_overlaps


def test_config_from_dict_rejects_unknown_keys():
    with pytest.raises(ConfigError):
        SanitizerConfig.from_dict({"not_a_real_key": 1})


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("PII_ENABLE_NER", "false")
    monkeypatch.setenv("PII_OCR_DPI_SCALE", "3.0")
    monkeypatch.setenv("PII_ENABLED_ENTITIES", "EMAIL,PHONE")
    cfg = SanitizerConfig().with_env_overrides()
    assert cfg.enable_ner is False
    assert cfg.ocr_dpi_scale == 3.0
    assert cfg.enabled_entities == ("EMAIL", "PHONE")


def test_overlap_resolution_prefers_higher_priority():
    # An SSN (priority 100) overlapping a PERSON (40) — SSN must win.
    ssn = Span(0, 11, "SSN", "123-45-6789", 0.9, "regex")
    person = Span(0, 20, "PERSON", "123-45-6789 Smith", 0.85, "spacy")
    kept = resolve_overlaps([person, ssn])
    assert len(kept) == 1
    assert kept[0].entity_type == "SSN"


def test_non_overlapping_spans_all_kept_and_sorted():
    a = Span(10, 15, "EMAIL", "x", 1.0)
    b = Span(0, 5, "PHONE", "y", 1.0)
    kept = resolve_overlaps([a, b])
    assert [s.entity_type for s in kept] == ["PHONE", "EMAIL"]  # sorted by start


def test_invalid_span_offsets_raise():
    with pytest.raises(ValueError):
        Span(5, 2, "EMAIL", "x")

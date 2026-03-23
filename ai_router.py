"""
AI Router — Processor Traien
Single entry point for all AI-enhanced features.

Backend priority (set in ai_config.json):
  "cloud"  → tries cloud_client first, falls back to ollama if enabled, then script
  "ollama" → tries ollama_client first, falls back to cloud if enabled, then script
  "script" → script-only, no AI calls

Each function returns (result, log_line) — same contract as the individual clients.
"""

import json
import os

_APP_DIR  = os.path.dirname(os.path.abspath(__file__))
_CFG_FILE = os.path.join(_APP_DIR, "ai_config.json")


# ─────────────────────────────────────────────────────────────────────────────
# Routing config
# ─────────────────────────────────────────────────────────────────────────────

def get_config() -> dict:
    if not os.path.exists(_CFG_FILE):
        return {"preferred_backend": "script", "fallback_enabled": True}
    try:
        with open(_CFG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"preferred_backend": "script", "fallback_enabled": True}


def save_config(preferred_backend: str, fallback_enabled: bool = True) -> dict:
    cfg = {
        "preferred_backend": preferred_backend,
        "fallback_enabled":  fallback_enabled,
    }
    with open(_CFG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    return cfg


def get_preferred_backend() -> str:
    """Returns 'cloud', 'ollama', or 'script'."""
    return get_config().get("preferred_backend", "script")


def get_status() -> dict:
    """
    Returns status of all three backends for display in settings.
    """
    import cloud_client as _cc
    import ollama_client as _oc

    cfg = get_config()
    preferred = cfg.get("preferred_backend", "script")
    fallback  = cfg.get("fallback_enabled", True)

    cc_cfg = _cc.get_config()
    oc_cfg = _oc.get_config()

    cloud_enabled  = bool(cc_cfg.get("enabled") and cc_cfg.get("api_key"))
    ollama_enabled = bool(oc_cfg.get("enabled"))

    return {
        "preferred":       preferred,
        "fallback":        fallback,
        "cloud_enabled":   cloud_enabled,
        "cloud_provider":  cc_cfg.get("provider", "claude"),
        "cloud_model":     cc_cfg.get("model", ""),
        "ollama_enabled":  ollama_enabled,
        "ollama_model":    oc_cfg.get("model", ""),
        "ollama_endpoint": oc_cfg.get("endpoint", ""),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Internal dispatcher
# ─────────────────────────────────────────────────────────────────────────────

def _dispatch(feature: str, cloud_fn, ollama_fn, script_result):
    """
    Try backends in preferred order. Returns first successful (non-empty) result.
    cloud_fn / ollama_fn: callables that return (result, log_line)
    script_result: what to return if all AI backends fail
    """
    cfg      = get_config()
    preferred = cfg.get("preferred_backend", "script")
    fallback  = cfg.get("fallback_enabled", True)

    if preferred == "script":
        return script_result, f"[SCRIPT] {feature}"

    # Build attempt order
    if preferred == "cloud":
        order = ["cloud", "ollama"] if fallback else ["cloud"]
    else:  # ollama
        order = ["ollama", "cloud"] if fallback else ["ollama"]

    for backend in order:
        if backend == "cloud":
            result, log = cloud_fn()
            if result:
                return result, log
        elif backend == "ollama":
            result, log = ollama_fn()
            if result:
                return result, log

    return script_result, f"[SCRIPT] {feature}  (all AI backends failed/disabled)"


# ─────────────────────────────────────────────────────────────────────────────
# Public feature API  (same signatures as ollama_client / cloud_client)
# ─────────────────────────────────────────────────────────────────────────────

def enhance_conditions(text: str, doc_type: str,
                       script_conditions: str) -> tuple[str, str]:
    import cloud_client as _cc
    import ollama_client as _oc
    return _dispatch(
        "condition_extraction",
        lambda: _cc.enhance_conditions(text, doc_type, script_conditions),
        lambda: _oc.enhance_conditions(text, doc_type, script_conditions),
        script_conditions,
    )


def interpret_guidelines(condition_text: str, chunks: list[dict]) -> tuple[str, str]:
    import cloud_client as _cc
    import ollama_client as _oc
    return _dispatch(
        "guideline_search",
        lambda: _cc.interpret_guidelines(condition_text, chunks),
        lambda: _oc.interpret_guidelines(condition_text, chunks),
        "",
    )


def draft_email_enhanced(conditions: list[dict], recipient_type: str,
                         language: str) -> tuple[str, str]:
    import cloud_client as _cc
    import ollama_client as _oc
    return _dispatch(
        "email_draft",
        lambda: _cc.draft_email_enhanced(conditions, recipient_type, language),
        lambda: _oc.draft_email_enhanced(conditions, recipient_type, language),
        "",
    )


def summarize_document(text: str, doc_type: str) -> tuple[str, str]:
    import cloud_client as _cc
    import ollama_client as _oc
    return _dispatch(
        "doc_summary",
        lambda: _cc.summarize_document(text, doc_type),
        lambda: _oc.summarize_document(text, doc_type),
        "",
    )

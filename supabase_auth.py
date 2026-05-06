"""
Supabase auth + per-user settings helpers for Streamlit.

This module keeps OAuth and user-level setting storage in one place so the UI
can stay simple.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request


def _supabase_url() -> str:
    return os.getenv("SUPABASE_URL", "").strip().rstrip("/")


def _public_key() -> str:
    return (
        os.getenv("SUPABASE_ANON_KEY", "").strip()
        or os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
    )


def _service_key() -> str:
    return (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
    )


def is_configured() -> bool:
    return bool(_supabase_url() and _public_key())


def _app_base_url() -> str:
    explicit = (
        os.getenv("PA_APP_URL", "").strip()
        or os.getenv("PUBLIC_APP_URL", "").strip()
        or os.getenv("APP_BASE_URL", "").strip()
    )
    if explicit:
        return explicit.rstrip("/")

    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if railway_domain:
        return f"https://{railway_domain}".rstrip("/")

    return "http://127.0.0.1:8501"


def get_google_redirect_url(flow_id: str = "", verifier: str = "") -> str:
    base = f"{_app_base_url()}/"
    params = {}
    if flow_id:
        params["pa_oauth_flow"] = flow_id
    if verifier:
        params["pa_oauth_v"] = verifier
    if not params:
        return base
    return f"{base}?{urllib.parse.urlencode(params)}"


def _json_request(method: str, url: str, payload: dict | None = None, *, api_key: str, bearer: str | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method.upper())
    req.add_header("apikey", api_key)
    req.add_header("Authorization", f"Bearer {bearer or api_key}")
    if payload is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return {"ok": True, "data": json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="ignore")
        try:
            data = json.loads(raw) if raw else {}
        except Exception:
            data = {"message": raw or str(e)}
        return {"ok": False, "status": e.code, "data": data}
    except Exception as e:
        return {"ok": False, "status": 0, "data": {"message": str(e)}}


def _pkce_verifier() -> str:
    return secrets.token_urlsafe(64)


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def begin_google_oauth() -> dict:
    """
    Create a Supabase Google OAuth URL using PKCE.
    Returns url + verifier/flow_id that the app should store.
    """
    if not is_configured():
        return {"ok": False, "error": "Supabase OAuth is not configured yet."}

    verifier = _pkce_verifier()
    flow_id = secrets.token_urlsafe(18)
    params = {
        "provider": "google",
        "redirect_to": get_google_redirect_url(flow_id, verifier),
        "code_challenge": _pkce_challenge(verifier),
        "code_challenge_method": "S256",
    }
    url = f"{_supabase_url()}/auth/v1/authorize?{urllib.parse.urlencode(params)}"
    return {"ok": True, "url": url, "verifier": verifier, "flow_id": flow_id}


def exchange_google_code(code: str, verifier: str) -> dict:
    """
    Exchange the OAuth code returned by Supabase for a session/user payload.
    """
    if not code or not verifier:
        return {"ok": False, "error": "Missing OAuth code or verifier."}
    if not is_configured():
        return {"ok": False, "error": "Supabase OAuth is not configured yet."}

    url = f"{_supabase_url()}/auth/v1/token?grant_type=pkce"
    result = _json_request(
        "POST",
        url,
        {"auth_code": code, "code_verifier": verifier},
        api_key=_public_key(),
        bearer=_public_key(),
    )
    if not result.get("ok"):
        data = result.get("data") or {}
        return {"ok": False, "error": data.get("message") or data.get("msg") or "Google sign-in failed."}

    data = result.get("data") or {}
    user = data.get("user") or {}
    meta = user.get("user_metadata") or {}
    return {
        "ok": True,
        "supabase_user_id": user.get("id"),
        "email": user.get("email", ""),
        "display_name": (
            meta.get("full_name")
            or meta.get("name")
            or meta.get("display_name")
            or user.get("email", "").split("@")[0]
        ),
        "role": meta.get("role") or "Processor",
        "user_metadata": meta,
        "session": data.get("session") or {},
    }


def _setting_key(user_key: str) -> str:
    return f"user_ai:{user_key}"


def load_user_gemini_key(user_key: str) -> str:
    if not user_key:
        return ""
    api_key = _service_key() or _public_key()
    if not _supabase_url() or not api_key:
        return ""

    params = urllib.parse.urlencode({"key": f"eq.{_setting_key(user_key)}", "select": "value_json"})
    url = f"{_supabase_url()}/rest/v1/settings?{params}"
    result = _json_request("GET", url, None, api_key=api_key, bearer=api_key)
    if not result.get("ok"):
        return ""

    rows = result.get("data") or []
    if not rows:
        return ""

    raw = rows[0].get("value_json")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return ""
    if isinstance(raw, dict):
        return str(raw.get("gemini_api_key", "")).strip()
    return ""


def save_user_gemini_key(user_key: str, gemini_api_key: str) -> dict:
    if not user_key:
        return {"ok": False, "error": "Missing user key."}
    api_key = _service_key() or _public_key()
    if not _supabase_url() or not api_key:
        return {"ok": False, "error": "Supabase settings storage is not configured."}

    payload = {
        "key": _setting_key(user_key),
        "value_json": json.dumps({"gemini_api_key": gemini_api_key.strip()}),
    }
    url = f"{_supabase_url()}/rest/v1/settings"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("apikey", api_key)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Prefer", "resolution=merge-duplicates")
    try:
        with urllib.request.urlopen(req, timeout=20):
            return {"ok": True}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="ignore")
        return {"ok": False, "error": raw or str(e)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

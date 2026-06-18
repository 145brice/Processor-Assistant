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
from datetime import datetime, timezone

try:
    from cryptography.fernet import Fernet
except Exception:
    Fernet = None


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
    url = _supabase_url()
    key = _public_key()
    if not url or not key:
        return False
    # Detect placeholder / example values that ship with the repo
    _placeholders = ("your-project.supabase.co", "your-anon-key", "your-project", "example.supabase.co")
    if any(p in url for p in _placeholders):
        return False
    if any(p in key for p in ("your-anon-key", "your-key", "anon-key-here", "key-here")):
        return False
    return True


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


def _profile_key(user_key: str) -> str:
    return f"user_profile:{user_key}"


def _browser_session_key(session_id: str) -> str:
    return f"browser_session:{session_id}"


def _current_user_email() -> str:
    try:
        import streamlit as st
        return str(st.session_state.get("user_email") or "").strip()
    except Exception:
        return ""


def _encryption_secret() -> str:
    return (
        os.getenv("PA_SETTINGS_ENCRYPTION_KEY", "").strip()
        or os.getenv("GEMINI_KEY_ENCRYPTION_SECRET", "").strip()
    )


def _fernet():
    secret = _encryption_secret()
    if not secret or Fernet is None:
        return None
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def _encrypt_secret(value: str) -> str:
    f = _fernet()
    if not f:
        return ""
    return f.encrypt(value.encode("utf-8")).decode("utf-8")


def _decrypt_secret(value: str) -> str:
    f = _fernet()
    if not f:
        return ""
    try:
        return f.decrypt(value.encode("utf-8")).decode("utf-8").strip()
    except Exception:
        return ""


def _settings_table_error(data: dict | str) -> str:
    text = json.dumps(data) if isinstance(data, dict) else str(data)
    if "public.settings" in text or "schema cache" in text or "PGRST205" in text:
        return (
            "Supabase settings storage is missing. Run SUPABASE_SCHEMA.sql in "
            "Supabase SQL Editor, then retry saving your Gemini key."
        )
    return text


def _extract_gemini_key_from_value_json(raw) -> str:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return ""
    if isinstance(raw, dict):
        if raw.get("gemini_api_key_enc"):
            return _decrypt_secret(str(raw.get("gemini_api_key_enc") or ""))
        # Backward compatibility for keys saved before app-side encryption.
        return str(raw.get("gemini_api_key", "")).strip()
    return ""


def load_user_gemini_key(user_key: str, user_email: str = "") -> str:
    if not user_key and not user_email:
        return ""
    api_key = _service_key() or _public_key()
    if not _supabase_url() or not api_key:
        return ""

    # Primary lookup by stable key.
    if user_key:
        params = urllib.parse.urlencode({
            "key": f"eq.{_setting_key(user_key)}",
            "select": "value_json,updated_at",
            "order": "updated_at.desc",
            "limit": "5",
        })
        url = f"{_supabase_url()}/rest/v1/settings?{params}"
        result = _json_request("GET", url, None, api_key=api_key, bearer=api_key)
        if result.get("ok"):
            rows = result.get("data") or []
            for row in rows:
                key = _extract_gemini_key_from_value_json(row.get("value_json"))
                if key:
                    return key

    # Fallback lookup by user email in case the stored user_key differs across auth paths.
    email = str(user_email or "").strip().lower()
    if email:
        params = urllib.parse.urlencode({
            "user_email": f"eq.{email}",
            "key": "like.user_ai:%",
            "select": "value_json,updated_at",
            "order": "updated_at.desc",
            "limit": "5",
        })
        url = f"{_supabase_url()}/rest/v1/settings?{params}"
        result = _json_request("GET", url, None, api_key=api_key, bearer=api_key)
        if result.get("ok"):
            rows = result.get("data") or []
            for row in rows:
                key = _extract_gemini_key_from_value_json(row.get("value_json"))
                if key:
                    return key
    return ""


def _load_setting_json(setting_key: str) -> dict:
    api_key = _service_key() or _public_key()
    if not setting_key or not _supabase_url() or not api_key:
        return {}
    params = urllib.parse.urlencode({"key": f"eq.{setting_key}", "select": "value_json"})
    url = f"{_supabase_url()}/rest/v1/settings?{params}"
    result = _json_request("GET", url, None, api_key=api_key, bearer=api_key)
    if not result.get("ok"):
        return {}
    rows = result.get("data") or []
    if not rows:
        return {}
    raw = rows[0].get("value_json")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return {}
    return raw if isinstance(raw, dict) else {}


def _save_setting_json(setting_key: str, value: dict, *, user_key: str = "", user_email: str = "") -> dict:
    api_key = _service_key() or _public_key()
    if not setting_key:
        return {"ok": False, "error": "Missing setting key."}
    if not _supabase_url() or not api_key:
        return {"ok": False, "error": "Supabase settings storage is not configured."}

    payload = {
        "key": setting_key,
        "user_key": user_key,
        "user_email": user_email or _current_user_email(),
        "value_json": json.dumps(value),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    url = f"{_supabase_url()}/rest/v1/settings"
    try:
        _upsert_setting(url, api_key, payload)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ensure_user_profile(user_key: str, *, email: str = "", display_name: str = "", role: str = "") -> dict:
    """Create or refresh the app-level user profile used for trial/subscription state."""
    if not user_key:
        return {}
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    profile = _load_setting_json(_profile_key(user_key))
    is_new = not profile
    if is_new:
        trial_end = (now + timedelta(days=14)).isoformat()
        profile = {
            "trial_started_at": now_iso,
            "trial_start_date": now.date().isoformat(),
            "trial_end_date": (now + timedelta(days=14)).date().isoformat(),
            "trial_days": 14,
            "subscription_status": "trialing",
            "plan": "beta",
            "terms_accepted_at": "",
        }
    else:
        # Back-fill trial_end_date for older profiles that don't have it
        if not profile.get("trial_end_date") and profile.get("trial_started_at"):
            try:
                start = datetime.fromisoformat(str(profile["trial_started_at"]).replace("Z", "+00:00"))
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                profile["trial_start_date"] = start.date().isoformat()
                profile["trial_end_date"] = (start + timedelta(days=14)).date().isoformat()
            except Exception:
                pass

    google_email = email or profile.get("google_email", "") or profile.get("email", "")
    profile.update({
        "user_key": user_key,
        "email": google_email,
        "google_email": google_email,
        "display_name": display_name or profile.get("display_name", ""),
        "role": role or profile.get("role", ""),
        "last_seen_at": now_iso,
    })
    save_result = _save_setting_json(_profile_key(user_key), profile, user_key=user_key, user_email=google_email)
    if not save_result.get("ok"):
        profile["_save_error"] = save_result.get("error") or "Supabase profile save failed."
    return profile


def accept_terms(user_key: str, *, email: str = "", display_name: str = "", role: str = "") -> dict:
    profile = ensure_user_profile(user_key, email=email, display_name=display_name, role=role)
    profile.pop("_save_error", None)
    profile["terms_accepted_at"] = datetime.now(timezone.utc).isoformat()
    save_result = _save_setting_json(_profile_key(user_key), profile, user_key=user_key, user_email=profile.get("email", email))
    if not save_result.get("ok"):
        profile["_save_error"] = save_result.get("error") or "Supabase terms save failed."
    return profile


def update_subscription_by_email(
    email: str,
    *,
    status: str,
    stripe_customer_id: str = "",
    stripe_subscription_id: str = "",
    plan: str = "beta",
) -> dict:
    """Update the app profile for a Stripe customer email."""
    email = (email or "").strip().lower()
    if not email:
        return {"ok": False, "error": "Missing customer email."}
    api_key = _service_key() or _public_key()
    if not _supabase_url() or not api_key:
        return {"ok": False, "error": "Supabase settings storage is not configured."}

    params = urllib.parse.urlencode({
        "user_email": f"eq.{email}",
        "select": "key,value_json,user_key,user_email",
    })
    url = f"{_supabase_url()}/rest/v1/settings?{params}"
    result = _json_request("GET", url, None, api_key=api_key, bearer=api_key)
    if not result.get("ok"):
        return {"ok": False, "error": _settings_table_error(result.get("data") or {})}

    rows = [
        row for row in (result.get("data") or [])
        if str(row.get("key", "")).startswith("user_profile:")
    ]
    if not rows:
        return {"ok": False, "error": f"No Processor Assistant profile found for {email}."}

    now = datetime.now(timezone.utc).isoformat()
    updated = 0
    for row in rows:
        raw = row.get("value_json") or {}
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = {}
        profile = raw if isinstance(raw, dict) else {}
        profile.update({
            "email": email,
            "stripe_email": email,
            "subscription_status": status,
            "plan": plan,
            "stripe_customer_id": stripe_customer_id or profile.get("stripe_customer_id", ""),
            "stripe_subscription_id": stripe_subscription_id or profile.get("stripe_subscription_id", ""),
            "subscription_updated_at": now,
        })
        save_result = _save_setting_json(
            row["key"],
            profile,
            user_key=row.get("user_key", ""),
            user_email=email,
        )
        if save_result.get("ok"):
            updated += 1
    return {"ok": bool(updated), "updated": updated}


def claim_subscription_by_email(stripe_email: str, current_user_key: str) -> dict:
    """Copy an active Stripe subscription from stripe_email's profile to current_user_key's profile.

    Used when someone paid with a different email than their Google sign-in.
    """
    stripe_email = (stripe_email or "").strip().lower()
    current_user_key = (current_user_key or "").strip()
    if not stripe_email or not current_user_key:
        return {"ok": False, "error": "Missing email or user key."}

    api_key = _service_key() or _public_key()
    if not _supabase_url() or not api_key:
        return {"ok": False, "error": "Supabase not configured."}

    # Look up the profile stored under the Stripe email
    params = urllib.parse.urlencode({"user_email": f"eq.{stripe_email}", "select": "key,value_json,user_key,user_email"})
    url = f"{_supabase_url()}/rest/v1/settings?{params}"
    result = _json_request("GET", url, None, api_key=api_key, bearer=api_key)
    if not result.get("ok"):
        return {"ok": False, "error": "Could not reach Supabase."}

    rows = [r for r in (result.get("data") or []) if str(r.get("key", "")).startswith("user_profile:")]
    if not rows:
        return {"ok": False, "error": f"No account found for {stripe_email}. Make sure you use the exact email you paid with."}

    source_profile = {}
    for row in rows:
        raw = row.get("value_json") or {}
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = {}
        if isinstance(raw, dict):
            source_profile = raw
            break

    status = str(source_profile.get("subscription_status") or "").lower()
    if status not in {"active", "paid", "beta_active", "trialing"}:
        return {"ok": False, "error": f"That account's subscription status is '{status or 'none'}' — not active. Contact support if you think this is wrong."}

    # Load current user's profile and merge subscription fields into it
    profile_key = _profile_key(current_user_key)
    params2 = urllib.parse.urlencode({"key": f"eq.{profile_key}", "select": "key,value_json,user_key,user_email"})
    url2 = f"{_supabase_url()}/rest/v1/settings?{params2}"
    result2 = _json_request("GET", url2, None, api_key=api_key, bearer=api_key)
    current_rows = (result2.get("data") or []) if result2.get("ok") else []
    current_profile = {}
    if current_rows:
        raw2 = current_rows[0].get("value_json") or {}
        if isinstance(raw2, str):
            try:
                raw2 = json.loads(raw2)
            except Exception:
                raw2 = {}
        current_profile = raw2 if isinstance(raw2, dict) else {}

    now = datetime.now(timezone.utc).isoformat()
    current_profile.update({
        "subscription_status": source_profile.get("subscription_status", status),
        "plan": source_profile.get("plan", "beta"),
        "stripe_customer_id": source_profile.get("stripe_customer_id", ""),
        "stripe_subscription_id": source_profile.get("stripe_subscription_id", ""),
        "subscription_updated_at": now,
        "stripe_email": stripe_email,
        "claimed_from_email": stripe_email,
    })

    current_email = current_profile.get("email") or ""
    save_result = _save_setting_json(profile_key, current_profile, user_key=current_user_key, user_email=current_email)
    if not save_result.get("ok"):
        return {"ok": False, "error": f"Found your subscription but could not save it: {save_result.get('error', 'unknown')}"}

    return {"ok": True, "status": status}


def save_user_gemini_key(user_key: str, gemini_api_key: str) -> dict:
    if not user_key:
        return {"ok": False, "error": "Missing user key."}
    api_key = _service_key() or _public_key()
    if not _supabase_url() or not api_key:
        return {"ok": False, "error": "Supabase settings storage is not configured."}

    clean_key = gemini_api_key.strip()
    encrypted_key = _encrypt_secret(clean_key)
    # Backward-compatible fallback: persist plaintext when encryption secret
    # is not configured so production users are not blocked from saving.
    # load_user_gemini_key() already supports this legacy/plain format.
    if encrypted_key:
        value_json = {
            "enc": "fernet-sha256-v1",
            "gemini_api_key_enc": encrypted_key,
        }
    else:
        value_json = {
            "enc": "none",
            "gemini_api_key": clean_key,
        }

    email_for_row = str(_current_user_email() or "").strip().lower()
    payload = {
        "key": _setting_key(user_key),
        "user_key": user_key,
        "user_email": email_for_row,
        "value_json": json.dumps(value_json),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    url = f"{_supabase_url()}/rest/v1/settings"
    try:
        if _upsert_setting(url, api_key, payload):
            # Read-after-write verification: if we cannot load what we just saved,
            # report it now so UI does not falsely imply durable save.
            read_back = load_user_gemini_key(user_key, user_email=email_for_row)
            if read_back:
                return {"ok": True}
            return {
                "ok": False,
                "error": (
                    "Saved request sent, but key could not be read back from Supabase. "
                    "Check settings table constraints/RLS and schema cache."
                ),
            }
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="ignore")
        try:
            data = json.loads(raw) if raw else {}
        except Exception:
            data = raw or str(e)
        text = json.dumps(data) if isinstance(data, dict) else str(data)
        if "user_email" in text or "user_key" in text or "schema cache" in text:
            return {
                "ok": False,
                "error": (
                    "Supabase settings columns exist in SQL but the API schema cache has not reloaded yet. "
                    "Run: notify pgrst, 'reload schema'; then save again."
                ),
            }
        return {"ok": False, "error": _settings_table_error(data)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _upsert_setting(url: str, api_key: str, payload: dict) -> bool:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("apikey", api_key)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Prefer", "resolution=merge-duplicates")
    with urllib.request.urlopen(req, timeout=20):
        return True


def save_browser_session(session_id: str, auth_data: dict, *, user_email: str = "") -> dict:
    """Persist a browser session auth snapshot for deploy-safe restores."""
    session_id = str(session_id or "").strip()
    if not session_id:
        return {"ok": False, "error": "Missing session id."}
    payload = dict(auth_data or {})
    payload["saved_at"] = datetime.now(timezone.utc).isoformat()
    return _save_setting_json(
        _browser_session_key(session_id),
        payload,
        user_key=session_id,
        user_email=(user_email or payload.get("user_email") or "").strip().lower(),
    )


def load_browser_session(session_id: str, *, max_age_days: int = 30) -> dict:
    """Load browser session auth snapshot if not expired."""
    session_id = str(session_id or "").strip()
    if not session_id:
        return {}
    data = _load_setting_json(_browser_session_key(session_id))
    if not data:
        return {}
    saved_at = str(data.get("saved_at") or "").strip()
    if saved_at:
        try:
            saved_dt = datetime.fromisoformat(saved_at.replace("Z", "+00:00"))
            if saved_dt.tzinfo is None:
                saved_dt = saved_dt.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - saved_dt).total_seconds() / 86400.0
            if age_days > max(1, int(max_age_days)):
                return {}
        except Exception:
            return {}
    return data if isinstance(data, dict) else {}


def clear_browser_session(session_id: str) -> dict:
    """Invalidate browser session snapshot."""
    session_id = str(session_id or "").strip()
    if not session_id:
        return {"ok": False, "error": "Missing session id."}
    return _save_setting_json(
        _browser_session_key(session_id),
        {},
        user_key=session_id,
        user_email="",
    )


def get_user_presence_counts(active_window_minutes: int = 15) -> dict:
    """Return all-time unique users plus 'active now' from profiles/sessions."""
    try:
        api_key = _service_key() or _public_key()
        if not _supabase_url() or not api_key:
            return {"ok": False, "error": "Supabase not configured.", "total_users": 0, "active_now": 0}

        def _fetch_rows(prefix: str) -> tuple[list, dict]:
            params = urllib.parse.urlencode({
                "key": f"like.{prefix}:%",
                "select": "key,value_json",
            })
            url = f"{_supabase_url()}/rest/v1/settings?{params}"
            result = _json_request("GET", url, None, api_key=api_key, bearer=api_key)
            return (result.get("data") or [], result)

        profile_rows, profile_result = _fetch_rows("user_profile")
        if not profile_result.get("ok"):
            return {"ok": False, "error": _settings_table_error(profile_result.get("data") or {}), "total_users": 0, "active_now": 0}
        session_rows, session_result = _fetch_rows("browser_session")
        if not session_result.get("ok"):
            session_rows = []

        now = datetime.now(timezone.utc)
        cutoff_seconds = max(1, int(active_window_minutes)) * 60
        active_identities = set()
        profile_identities = set()
        session_identities = set()

        def _payload(row: dict) -> dict:
            raw = row.get("value_json") or {}
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except Exception:
                    raw = {}
            return raw if isinstance(raw, dict) else {}

        def _identity(raw: dict, fallback: str = "") -> str:
            email = str(raw.get("email") or raw.get("google_email") or raw.get("user_email") or "").strip().lower()
            if email:
                return f"email:{email}"
            user_key = str(raw.get("user_key") or raw.get("supabase_user_id") or raw.get("user_id") or "").strip()
            if user_key:
                return f"user:{user_key}"
            fallback = str(fallback or "").strip()
            return f"key:{fallback}" if fallback else ""

        def _is_recent(raw: dict, field_names: tuple[str, ...]) -> bool:
            for field_name in field_names:
                timestamp = str(raw.get(field_name) or "").strip()
                if not timestamp:
                    continue
                try:
                    seen_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if seen_at.tzinfo is None:
                        seen_at = seen_at.replace(tzinfo=timezone.utc)
                    return (now - seen_at).total_seconds() <= cutoff_seconds
                except Exception:
                    continue
            return False

        for row in profile_rows:
            key = str(row.get("key", ""))
            if not key.startswith("user_profile:"):
                continue
            raw = _payload(row)
            identity = _identity(raw, key.removeprefix("user_profile:"))
            if not identity:
                continue
            profile_identities.add(identity)
            if _is_recent(raw, ("last_seen_at", "saved_at")):
                active_identities.add(identity)

        for row in session_rows:
            key = str(row.get("key", ""))
            if not key.startswith("browser_session:"):
                continue
            raw = _payload(row)
            if not raw.get("authenticated"):
                continue
            identity = _identity(raw, key.removeprefix("browser_session:"))
            if not identity:
                continue
            session_identities.add(identity)
            if _is_recent(raw, ("saved_at", "last_seen_at")):
                active_identities.add(identity)

        all_identities = profile_identities | session_identities

        return {
            "ok": True,
            "total_users": len(all_identities),
            "all_time_unique_users": len(all_identities),
            "profile_users": len(profile_identities),
            "session_users": len(session_identities),
            "active_now": len(active_identities),
            "window_minutes": int(active_window_minutes),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "total_users": 0, "all_time_unique_users": 0, "active_now": 0}

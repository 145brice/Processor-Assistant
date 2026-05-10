"""In-app chat storage for Processor Assistant.

Messages are app metadata, not uploaded documents. They are stored in the
Supabase settings table so signed-in users can see the same shared chat.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


_CHAT_KEY = "app_chat:global"
_MAX_MESSAGES = 300
_LOCAL_CHAT_FILE = os.path.join(os.path.dirname(__file__), "chat_messages.json")


def _supabase_url() -> str:
    return os.getenv("SUPABASE_URL", "").strip().rstrip("/")


def _service_key() -> str:
    return (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
    )


def _json_request(method: str, url: str, payload: dict | None = None) -> dict:
    api_key = _service_key()
    if not _supabase_url() or not api_key:
        return {"ok": False, "error": "Supabase service storage is not configured."}

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method.upper())
    req.add_header("apikey", api_key)
    req.add_header("Authorization", f"Bearer {api_key}")
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return {"ok": True, "data": json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="ignore")
        return {"ok": False, "status": exc.code, "error": raw or str(exc)}
    except Exception as exc:
        return {"ok": False, "status": 0, "error": str(exc)}


def _load_local() -> list[dict]:
    try:
        with open(_LOCAL_CHAT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_local(messages: list[dict]) -> None:
    with open(_LOCAL_CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(messages[-_MAX_MESSAGES:], f, indent=2, ensure_ascii=False)


def load_messages(limit: int = 80) -> list[dict]:
    """Return newest chat messages in chronological display order."""
    params = urllib.parse.urlencode({"key": f"eq.{_CHAT_KEY}", "select": "value_json"})
    url = f"{_supabase_url()}/rest/v1/settings?{params}"
    result = _json_request("GET", url)
    if not result.get("ok"):
        messages = _load_local()
        return messages[-limit:]

    rows = result.get("data") or []
    if not rows:
        return []
    raw = rows[0].get("value_json")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = {}
    messages = raw.get("messages", []) if isinstance(raw, dict) else []
    if not isinstance(messages, list):
        messages = []
    return messages[-limit:]


def save_message(*, user_key: str, user_name: str, user_email: str, text: str) -> dict:
    """Append a chat message and keep a bounded rolling history."""
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "Message is empty."}
    if len(text) > 2000:
        return {"ok": False, "error": "Message is too long. Keep it under 2,000 characters."}

    messages = load_messages(limit=_MAX_MESSAGES)
    message = {
        "id": f"{int(datetime.now(timezone.utc).timestamp() * 1000)}:{user_key or user_email}",
        "ts": datetime.now(timezone.utc).isoformat(),
        "user_key": user_key,
        "user_name": user_name or user_email or "User",
        "user_email": user_email,
        "text": text,
    }
    messages.append(message)
    messages = messages[-_MAX_MESSAGES:]

    payload = {
        "key": _CHAT_KEY,
        "user_key": "",
        "user_email": "",
        "value_json": json.dumps({"messages": messages}),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    url = f"{_supabase_url()}/rest/v1/settings"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    api_key = _service_key()
    if not _supabase_url() or not api_key:
        _save_local(messages)
        return {"ok": True, "local": True}
    req.add_header("apikey", api_key)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Prefer", "resolution=merge-duplicates")
    try:
        with urllib.request.urlopen(req, timeout=20):
            return {"ok": True}
    except Exception as exc:
        _save_local(messages)
        return {"ok": False, "error": str(exc)}

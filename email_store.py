"""Account-scoped, encrypted inbox configuration storage."""

import base64
import hashlib
import json
import os
import tempfile
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


def data_dir() -> Path:
    return Path(os.getenv("PA_EMAIL_DATA_DIR") or os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
                or Path(__file__).parent / "email_data")


def account_dir(user_key: str) -> Path:
    if not user_key or user_key == "sandbox":
        raise ValueError("Sign in to a real account to use Email Watch.")
    return data_dir() / hashlib.sha256(user_key.encode()).hexdigest()


def cipher() -> Fernet:
    secret = os.getenv("PA_SETTINGS_ENCRYPTION_KEY", "").strip()
    if not secret:
        raise ValueError("Email credential encryption is not configured. Contact support.")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()))


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _cloud():
    import supabase_auth as auth
    # Never fall back to an anonymous database credential for private storage.
    if auth._supabase_url() and os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip():
        return auth
    if os.getenv("RAILWAY_ENVIRONMENT_ID"):
        raise ValueError("Durable email settings storage is not configured. Contact support.")
    return None


def _cloud_load(auth, user_key: str):
    import urllib.parse
    params = urllib.parse.urlencode({"key": "eq.email_watch:" + user_key,
                                    "user_key": "eq." + user_key,
                                    "select": "value_json", "limit": "1"})
    result = auth._json_request("GET", auth._supabase_url() + "/rest/v1/settings?" + params,
                                api_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
                                bearer=os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    if not result.get("ok"):
        raise ValueError("Could not load your saved email settings. Please retry.")
    rows = result.get("data") or []
    if not rows:
        return {}
    raw = rows[0]["value_json"]
    return json.loads(raw) if isinstance(raw, str) else raw


def load(user_key: str) -> dict:
    directory = account_dir(user_key)
    auth = _cloud()
    if auth:
        stored = _cloud_load(auth, user_key)
    else:
        path = directory / "config.json"
        stored = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not stored:
        return {}
    try:
        envelope = json.loads(cipher().decrypt(stored["encrypted"].encode()))
        if envelope["user_key"] != user_key:
            raise ValueError("Account mismatch")
        return envelope["config"]
    except (InvalidToken, KeyError, TypeError, json.JSONDecodeError, ValueError):
        raise ValueError("Could not decrypt your email settings. Contact support before replacing them.") from None


def save(user_key: str, config: dict) -> None:
    directory = account_dir(user_key)
    encrypted = cipher().encrypt(json.dumps({"user_key": user_key, "config": config}).encode()).decode()
    stored = {"version": 1, "encrypted": encrypted}
    auth = _cloud()
    if auth:
        result = auth._save_setting_json("email_watch:" + user_key, stored, user_key=user_key)
        if not result.get("ok"):
            raise ValueError("Could not save your email settings. Please retry.")
        if _cloud_load(auth, user_key) != stored:
            raise ValueError("Email settings could not be verified after saving. Please retry.")
    else:
        atomic_json(directory / "config.json", stored)
    if load(user_key) != config:
        raise ValueError("Email settings could not be verified after saving. Please retry.")


def delete(user_key: str) -> None:
    directory = account_dir(user_key)
    auth = _cloud()
    if auth:
        result = auth._save_setting_json("email_watch:" + user_key, {}, user_key=user_key)
        if not result.get("ok") or _cloud_load(auth, user_key):
            raise ValueError("Could not remove your saved email credentials. Please retry.")
    path = directory / "config.json"
    if path.exists():
        path.unlink()

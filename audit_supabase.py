"""
Production Supabase audit for Processor Assistant.

Reads SUPABASE_URL plus a service-role/secret key from the environment or .env,
then prints counts for Auth users, app profiles, browser sessions, and mirrored
loan rows. It intentionally does not print API keys or full user records.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


DEFAULT_SINCE = "2026-05-10T05:51:26+00:00"


def _load_env() -> None:
    if not load_dotenv:
        return
    here = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(here, ".env"), override=False)
    load_dotenv(os.path.join(os.path.dirname(here), ".env"), override=False)


def _service_key() -> str:
    return (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
    )


def _request(method: str, url: str, key: str):
    req = urllib.request.Request(url, method=method)
    req.add_header("apikey", key)
    req.add_header("Authorization", f"Bearer {key}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code}: {raw or e.reason}") from e


def _dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _count_since(rows: list[dict], field: str, since: datetime) -> int:
    total = 0
    for row in rows:
        value = _dt(str(row.get(field) or ""))
        if value and value >= since:
            total += 1
    return total


def _rest_rows(base_url: str, key: str, table: str, params: dict[str, str]) -> list[dict]:
    query = urllib.parse.urlencode(params)
    url = f"{base_url}/rest/v1/{urllib.parse.quote(table)}?{query}"
    data = _request("GET", url, key)
    return data if isinstance(data, list) else []


def main() -> int:
    _load_env()
    base_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = _service_key()
    since = _dt(os.getenv("PA_AUDIT_SINCE", "").strip() or DEFAULT_SINCE)
    if not since:
        print(f"Invalid PA_AUDIT_SINCE. Use ISO format, e.g. {DEFAULT_SINCE}", file=sys.stderr)
        return 2
    if not base_url or "your-project.supabase.co" in base_url:
        print("Missing real SUPABASE_URL.", file=sys.stderr)
        return 2
    if not key or key.startswith("your-"):
        print("Missing service-role/secret SUPABASE key.", file=sys.stderr)
        return 2

    print(f"Audit since: {since.isoformat()}")

    auth_users = []
    try:
        page = 1
        while True:
            url = f"{base_url}/auth/v1/admin/users?{urllib.parse.urlencode({'page': page, 'per_page': 1000})}"
            data = _request("GET", url, key) or {}
            users = data.get("users") or []
            auth_users.extend(users)
            if len(users) < 1000:
                break
            page += 1
    except Exception as e:
        print(f"Auth users: query failed: {e}")

    if auth_users:
        created_since = _count_since(auth_users, "created_at", since)
        signed_since = _count_since(auth_users, "last_sign_in_at", since)
        confirmed = len([u for u in auth_users if u.get("email_confirmed_at") or u.get("confirmed_at")])
        print(f"Auth users total: {len(auth_users)}")
        print(f"Auth users created since: {created_since}")
        print(f"Auth users signed in since: {signed_since}")
        print(f"Auth users confirmed total: {confirmed}")
        print("Recent auth users:")
        for user in sorted(auth_users, key=lambda u: str(u.get("created_at") or ""), reverse=True)[:10]:
            print(
                f"- {user.get('email', '')} | created={user.get('created_at', '')} "
                f"| last_sign_in={user.get('last_sign_in_at', '')}"
            )

    checks = [
        ("App profile rows", "settings", {"select": "key,user_email,updated_at", "key": "like.user_profile:%"}),
        ("Browser session rows", "settings", {"select": "key,user_email,updated_at", "key": "like.browser_session:%"}),
        ("Mirrored loan rows", "loans", {"select": "id,loan_num,borrower,updated_at"}),
    ]
    for label, table, params in checks:
        try:
            rows = _rest_rows(base_url, key, table, params)
            print(f"{label} total: {len(rows)}")
            print(f"{label} updated since: {_count_since(rows, 'updated_at', since)}")
        except Exception as e:
            print(f"{label}: query failed: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

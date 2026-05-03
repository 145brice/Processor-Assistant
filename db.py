"""
Local SQLite Database for Processor Assistant
Fully offline - no cloud, no Supabase.
Stores user accounts and scan history locally.
"""

import os
import sqlite3
import hashlib
import json
import urllib.request
import urllib.error
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "processor.db")


ROLE_OPTIONS = ["Processor", "Loan Officer", "Jr Underwriter", "Manager"]


def _get_conn():
    """Get SQLite connection, create tables if needed."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT DEFAULT '',
            role TEXT DEFAULT 'Processor',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    # Migrate existing DBs that don't have display_name / role columns
    try:
        conn.execute("ALTER TABLE users ADD COLUMN display_name TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'Processor'")
        conn.commit()
    except Exception:
        pass
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            doc_type TEXT,
            conditions TEXT,
            risks TEXT,
            bank_rules TEXT,
            summary TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _supabase_url() -> str:
    return os.getenv("SUPABASE_URL", "").strip().rstrip("/")


def _supabase_service_key() -> str:
    return (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
        or os.getenv("SUPABASE_SECRET_KEY", "").strip()
    )


def _supabase_public_key() -> str:
    return (
        os.getenv("SUPABASE_ANON_KEY", "").strip()
        or os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
    )


def _supabase_post(path: str, payload: dict, api_key: str, bearer: str | None = None) -> dict:
    url = f"{_supabase_url()}{path}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("apikey", api_key)
    req.add_header("Authorization", f"Bearer {bearer or api_key}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            return {"ok": True, "data": json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="ignore")
        try:
            data = json.loads(raw) if raw else {}
        except Exception:
            data = {"message": raw}
        return {"ok": False, "status": e.code, "data": data}
    except Exception as e:
        return {"ok": False, "status": 0, "data": {"message": str(e)}}


def _sync_user_to_supabase_auth(email: str, password: str, display_name: str, role: str) -> dict:
    """
    Create user in Supabase Auth so it appears in Authentication > Users.
    Prefers admin endpoint (service role). Falls back to public signup.
    """
    url = _supabase_url()
    if not url:
        return {"ok": False, "error": "SUPABASE_URL missing"}

    service_key = _supabase_service_key()
    public_key = _supabase_public_key()

    payload = {
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"display_name": display_name, "role": role},
    }

    if service_key:
        r = _supabase_post("/auth/v1/admin/users", payload, service_key, bearer=service_key)
        if r["ok"]:
            user = r["data"] or {}
            return {"ok": True, "id": user.get("id"), "email": user.get("email", email)}
        msg = str((r.get("data") or {}).get("msg") or (r.get("data") or {}).get("message") or "").lower()
        if "already" in msg or "exists" in msg:
            return {"ok": True, "id": None, "email": email}
        return {"ok": False, "error": (r.get("data") or {}).get("message") or (r.get("data") or {}).get("msg") or "Supabase auth create failed"}

    if public_key:
        signup_payload = {
            "email": email,
            "password": password,
            "data": {"display_name": display_name, "role": role},
        }
        r = _supabase_post("/auth/v1/signup", signup_payload, public_key)
        if r["ok"]:
            user = (r["data"] or {}).get("user") or {}
            return {"ok": True, "id": user.get("id"), "email": user.get("email", email)}
        msg = str((r.get("data") or {}).get("msg") or (r.get("data") or {}).get("message") or "").lower()
        if "already" in msg or "exists" in msg:
            return {"ok": True, "id": None, "email": email}
        return {"ok": False, "error": (r.get("data") or {}).get("message") or (r.get("data") or {}).get("msg") or "Supabase signup failed"}

    return {"ok": False, "error": "No Supabase auth key configured (need service role or anon/publishable key)"}


# --- Auth ---

def signup(email: str, password: str, display_name: str = "", role: str = "Processor") -> dict:
    try:
        email = (email or "").strip().lower()
        display_name = (display_name or "").strip()
        # Ensure real Supabase Auth user is created when Supabase is configured.
        if _supabase_url() and (_supabase_service_key() or _supabase_public_key()):
            sb = _sync_user_to_supabase_auth(email, password, display_name, role)
            if not sb.get("ok"):
                return {"error": f"Supabase auth error: {sb.get('error')}"}

        conn = _get_conn()
        pw_hash = _hash_password(password)
        conn.execute(
            "INSERT INTO users (email, password_hash, display_name, role) VALUES (?, ?, ?, ?)",
            (email, pw_hash, display_name, role),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()
        try:
            import supabase_sync
            supabase_sync.mirror_user({
                "id": str(row["id"]), "email": email, "password_hash": pw_hash,
                "display_name": display_name, "role": role,
            })
        except Exception:
            pass
        return {"success": True, "user_id": str(row["id"]), "email": email,
                "display_name": display_name, "role": role}
    except sqlite3.IntegrityError:
        return {"error": "Email already registered"}
    except Exception as e:
        return {"error": str(e)}


def login(email: str, password: str) -> dict:
    try:
        email = (email or "").strip().lower()
        conn = _get_conn()
        row = conn.execute(
            "SELECT id, password_hash, display_name, role FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()
        if row and row["password_hash"] == _hash_password(password):
            # Backfill legacy local users into Supabase Auth when configured.
            if _supabase_url() and (_supabase_service_key() or _supabase_public_key()):
                _ = _sync_user_to_supabase_auth(
                    email=email,
                    password=password,
                    display_name=row["display_name"] or "",
                    role=row["role"] or "Processor",
                )
            return {
                "success": True,
                "user_id": str(row["id"]),
                "email": email,
                "display_name": row["display_name"] or "",
                "role": row["role"] or "Processor",
            }
        return {"error": "Invalid email or password"}
    except Exception as e:
        return {"error": str(e)}


def get_all_users() -> list:
    """Return all users (for pipeline assignment dropdowns)."""
    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT id, email, display_name, role FROM users ORDER BY display_name, email"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def logout():
    pass  # Nothing to do for local auth


# --- Scan History ---

def save_result(user_id: str, doc_type: str, conditions: str, risks: str, bank_rules: str = "") -> dict:
    try:
        summary = conditions[:200] + "..." if len(conditions) > 200 else conditions
        conn = _get_conn()
        cur = conn.execute(
            "INSERT INTO scan_history (user_id, doc_type, conditions, risks, bank_rules, summary) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, doc_type, conditions, risks, bank_rules, summary),
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return {"success": True, "id": row_id}
    except Exception as e:
        return {"error": str(e)}


def get_history(user_id: str, limit: int = 20) -> list[dict]:
    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT id, doc_type, summary, conditions, risks, bank_rules, created_at "
            "FROM scan_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_file_count(user_id: str) -> int:
    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM scan_history WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        conn.close()
        return row["cnt"] if row else 0
    except Exception:
        return 0


def log_pattern(doc_type: str, rule_results: dict) -> None:
    """Log anonymized pattern data locally. Non-critical."""
    try:
        conn = _get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_type TEXT,
                rule_results TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute(
            "INSERT INTO admin_patterns (doc_type, rule_results) VALUES (?, ?)",
            (doc_type, json.dumps(rule_results)),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

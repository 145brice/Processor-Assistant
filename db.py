"""
Local SQLite Database for Processor Traien
Fully offline - no cloud, no Supabase.
Stores user accounts and scan history locally.
"""

import os
import sqlite3
import hashlib
import json
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


# --- Auth ---

def signup(email: str, password: str, display_name: str = "", role: str = "Processor") -> dict:
    try:
        conn = _get_conn()
        conn.execute(
            "INSERT INTO users (email, password_hash, display_name, role) VALUES (?, ?, ?, ?)",
            (email, _hash_password(password), display_name.strip(), role),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()
        return {"success": True, "user_id": str(row["id"]), "email": email,
                "display_name": display_name, "role": role}
    except sqlite3.IntegrityError:
        return {"error": "Email already registered"}
    except Exception as e:
        return {"error": str(e)}


def login(email: str, password: str) -> dict:
    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT id, password_hash, display_name, role FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()
        if row and row["password_hash"] == _hash_password(password):
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

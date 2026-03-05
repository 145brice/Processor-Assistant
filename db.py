"""
Supabase Database Helpers for Processor Traien
Stores ONLY structured results - never raw documents or PII.
"""

import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_supabase():
    """Get or create Supabase client singleton."""
    global _client
    if _client is None:
        from supabase import create_client

        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        if not url or not key:
            return None
        _client = create_client(url, key)
    return _client


# --- Auth ---


def signup(email: str, password: str) -> dict:
    """Sign up a new user via Supabase auth."""
    sb = get_supabase()
    if not sb:
        return {"error": "Supabase not configured"}
    try:
        result = sb.auth.sign_up({"email": email, "password": password})
        if result.user:
            return {"success": True, "user_id": result.user.id, "email": email}
        return {"error": "Signup failed - check email/password requirements"}
    except Exception as e:
        return {"error": str(e)}


def login(email: str, password: str) -> dict:
    """Log in an existing user."""
    sb = get_supabase()
    if not sb:
        return {"error": "Supabase not configured"}
    try:
        result = sb.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        if result.user:
            return {"success": True, "user_id": result.user.id, "email": email}
        return {"error": "Login failed - check credentials"}
    except Exception as e:
        return {"error": str(e)}


def logout():
    """Log out current user."""
    sb = get_supabase()
    if sb:
        try:
            sb.auth.sign_out()
        except Exception:
            pass


# --- Scan History (structured data only, no raw docs) ---


def save_result(user_id: str, doc_type: str, conditions: str, risks: str, bank_rules: str = "") -> dict:
    """Save scan results. Only structured output - never raw document text."""
    sb = get_supabase()
    if not sb:
        return {"error": "Supabase not configured"}
    try:
        # Create a brief summary (first 200 chars of conditions) for history display
        summary = conditions[:200] + "..." if len(conditions) > 200 else conditions

        data = {
            "user_id": user_id,
            "doc_type": doc_type,
            "conditions": conditions,
            "risks": risks,
            "bank_rules": bank_rules,
            "summary": summary,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = sb.table("scan_history").insert(data).execute()
        return {"success": True, "id": result.data[0]["id"] if result.data else None}
    except Exception as e:
        return {"error": str(e)}


def get_history(user_id: str, limit: int = 20) -> list[dict]:
    """Fetch user's scan history. Returns structured results only."""
    sb = get_supabase()
    if not sb:
        return []
    try:
        result = (
            sb.table("scan_history")
            .select("id, doc_type, summary, conditions, risks, bank_rules, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def get_file_count(user_id: str) -> int:
    """Count how many live files the user has submitted."""
    sb = get_supabase()
    if not sb:
        return 0
    try:
        result = (
            sb.table("scan_history")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        return result.count or 0
    except Exception:
        return 0


# --- Admin Pattern Logging (anonymized, no PII) ---


def log_pattern(doc_type: str, rule_results: dict) -> None:
    """
    Log anonymized pattern data for admin learning.
    NO PII, NO raw text - only rule pass/fail counts.
    """
    sb = get_supabase()
    if not sb:
        return
    try:
        data = {
            "doc_type": doc_type,
            "rule_results": json.dumps(rule_results),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        sb.table("admin_patterns").insert(data).execute()
    except Exception:
        pass  # Non-critical, don't break user flow

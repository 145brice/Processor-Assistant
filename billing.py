"""
Billing & Usage Tracker — Processor Traien
Tracks monthly document scans per user and calculates costs.

Pricing model:
  $49 / month  — base subscription (includes INCLUDED_FILES scans)
  $10 / file   — each scan over the monthly threshold
  Resets on the 1st of each month (UTC).

All data is stored locally in processor.db — no payment processor, no cloud.
This module tracks usage only; no real charges are made here.
"""

import os
import sqlite3
from datetime import datetime

_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "processor.db")

# ── Pricing constants ───────────────────────────────────────────────────────
MONTHLY_BASE      = 49.00   # flat monthly fee
INCLUDED_FILES    = 50      # scans included in base price
OVERAGE_RATE      = 10.00   # per scan over threshold


# ─────────────────────────────────────────────────────────────────────────────
# DB setup
# ─────────────────────────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS billing_events (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT    NOT NULL,
            year_month TEXT    NOT NULL,   -- 'YYYY-MM'
            doc_type   TEXT    DEFAULT '',
            scan_count INTEGER DEFAULT 1,
            logged_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS billing_notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT    NOT NULL,
            year_month TEXT    NOT NULL,
            note       TEXT    DEFAULT '',
            created_at TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# Log a scan
# ─────────────────────────────────────────────────────────────────────────────

def log_scan(user_id: str, doc_type: str = "") -> dict:
    """
    Record one document scan for the current calendar month.
    Returns updated usage dict for this month.
    """
    ym = _current_month()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO billing_events (user_id, year_month, doc_type) VALUES (?, ?, ?)",
        (user_id, ym, doc_type),
    )
    conn.commit()
    conn.close()
    return get_usage(user_id, ym)


# ─────────────────────────────────────────────────────────────────────────────
# Usage query
# ─────────────────────────────────────────────────────────────────────────────

def get_usage(user_id: str, year_month: str | None = None) -> dict:
    """
    Return usage and cost for a given month (defaults to current month).

    Returns:
        year_month      — 'YYYY-MM'
        scans           — total scans this month
        included        — how many are covered by base
        overage         — scans above threshold
        base_cost       — $49.00
        overage_cost    — overage × $10.00
        total_cost      — base + overage
        pct_used        — % of included quota used (capped at 100 for display)
        by_doc_type     — {doc_type: count}
    """
    ym   = year_month or _current_month()
    conn = _get_conn()
    rows = conn.execute(
        "SELECT doc_type, COUNT(*) as cnt FROM billing_events "
        "WHERE user_id = ? AND year_month = ? GROUP BY doc_type",
        (user_id, ym),
    ).fetchall()
    conn.close()

    by_type = {r["doc_type"] or "Unknown": r["cnt"] for r in rows}
    total   = sum(by_type.values())
    overage = max(0, total - INCLUDED_FILES)
    over_cost = round(overage * OVERAGE_RATE, 2)

    return {
        "year_month":   ym,
        "scans":        total,
        "included":     INCLUDED_FILES,
        "overage":      overage,
        "base_cost":    MONTHLY_BASE,
        "overage_cost": over_cost,
        "total_cost":   round(MONTHLY_BASE + over_cost, 2),
        "pct_used":     min(100, round(total / INCLUDED_FILES * 100)),
        "by_doc_type":  by_type,
    }


def get_history(user_id: str, months: int = 6) -> list[dict]:
    """
    Return usage summary for the last N calendar months (newest first).
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT year_month, COUNT(*) as cnt FROM billing_events "
        "WHERE user_id = ? GROUP BY year_month ORDER BY year_month DESC LIMIT ?",
        (user_id, months),
    ).fetchall()
    conn.close()

    result = []
    for r in rows:
        ym       = r["year_month"]
        total    = r["cnt"]
        overage  = max(0, total - INCLUDED_FILES)
        over_cost = round(overage * OVERAGE_RATE, 2)
        result.append({
            "year_month":   ym,
            "scans":        total,
            "overage":      overage,
            "total_cost":   round(MONTHLY_BASE + over_cost, 2),
        })
    return result


def get_all_users_usage(year_month: str | None = None) -> list[dict]:
    """Admin view — usage for every user in a given month."""
    ym   = year_month or _current_month()
    conn = _get_conn()
    rows = conn.execute(
        "SELECT b.user_id, u.email, u.display_name, u.role, COUNT(*) as cnt "
        "FROM billing_events b "
        "LEFT JOIN users u ON CAST(u.id AS TEXT) = b.user_id "
        "WHERE b.year_month = ? GROUP BY b.user_id ORDER BY cnt DESC",
        (ym,),
    ).fetchall()
    conn.close()

    result = []
    for r in rows:
        total    = r["cnt"]
        overage  = max(0, total - INCLUDED_FILES)
        over_cost = round(overage * OVERAGE_RATE, 2)
        result.append({
            "user_id":      r["user_id"],
            "email":        r["email"] or r["user_id"],
            "display_name": r["display_name"] or "",
            "role":         r["role"] or "",
            "scans":        total,
            "overage":      overage,
            "total_cost":   round(MONTHLY_BASE + over_cost, 2),
        })
    return result


def add_note(user_id: str, note: str, year_month: str | None = None):
    """Attach a billing note for the month (e.g. 'Batch of 5 rush closings')."""
    ym = year_month or _current_month()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO billing_notes (user_id, year_month, note) VALUES (?, ?, ?)",
        (user_id, ym, note.strip()),
    )
    conn.commit()
    conn.close()


def get_notes(user_id: str, year_month: str | None = None) -> list[str]:
    ym = year_month or _current_month()
    conn = _get_conn()
    rows = conn.execute(
        "SELECT note FROM billing_notes WHERE user_id = ? AND year_month = ? "
        "ORDER BY created_at",
        (user_id, ym),
    ).fetchall()
    conn.close()
    return [r["note"] for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _current_month() -> str:
    return datetime.utcnow().strftime("%Y-%m")


def format_month(ym: str) -> str:
    """'2026-03' → 'March 2026'"""
    try:
        return datetime.strptime(ym, "%Y-%m").strftime("%B %Y")
    except Exception:
        return ym

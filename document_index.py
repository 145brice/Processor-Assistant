"""
Document Index — fast SQLite-backed search for scanned mortgage docs.
Stores title + key metadata so the Reader never re-scans PDFs on every search.
"""

import sqlite3
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = str(Path(__file__).parent / "document_index.db")


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path     TEXT NOT NULL UNIQUE,
                file_name     TEXT,
                borrower      TEXT,
                loan_number   TEXT,
                doc_type      TEXT,
                month         TEXT,
                year          TEXT,
                key_points    TEXT,
                indexed_at    TEXT
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_borrower  ON documents(borrower)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_doc_type  ON documents(doc_type)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_loan_num  ON documents(loan_number)")


def index_document(
    file_path: str,
    borrower: Optional[str] = None,
    loan_number: Optional[str] = None,
    doc_type: Optional[str] = None,
    key_points: Optional[str] = None,
):
    """Add or update a document in the index. Called after every scan/save."""
    init_db()
    file_path = str(Path(file_path).resolve())
    file_name = Path(file_path).name

    # Derive month/year from key_points or today
    month, year = _extract_date(key_points or "")
    if not month:
        now = datetime.now()
        month, year = now.strftime("%B"), str(now.year)

    with _conn() as c:
        c.execute("""
            INSERT INTO documents
                (file_path, file_name, borrower, loan_number, doc_type, month, year, key_points, indexed_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(file_path) DO UPDATE SET
                borrower=excluded.borrower,
                loan_number=excluded.loan_number,
                doc_type=excluded.doc_type,
                month=excluded.month,
                year=excluded.year,
                key_points=excluded.key_points,
                indexed_at=excluded.indexed_at
        """, (file_path, file_name, borrower, loan_number, doc_type,
              month, year, key_points, datetime.now().isoformat()))


def search(query: str, limit: int = 30):
    """
    Fast search across borrower, loan#, doc type, key points, filename.
    Returns list of dicts.
    """
    init_db()
    q = f"%{query.strip()}%"
    with _conn() as c:
        rows = c.execute("""
            SELECT file_path, file_name, borrower, loan_number, doc_type, month, year, key_points, indexed_at
            FROM documents
            WHERE borrower    LIKE ? OR
                  loan_number LIKE ? OR
                  doc_type    LIKE ? OR
                  key_points  LIKE ? OR
                  file_name   LIKE ? OR
                  month       LIKE ? OR
                  year        LIKE ?
            ORDER BY indexed_at DESC
            LIMIT ?
        """, (q, q, q, q, q, q, q, limit)).fetchall()
    return [dict(r) for r in rows]


def remove_document(file_path: str):
    init_db()
    file_path = str(Path(file_path).resolve())
    with _conn() as c:
        c.execute("DELETE FROM documents WHERE file_path=?", (file_path,))


def get_all(limit: int = 200):
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM documents ORDER BY indexed_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def _extract_date(text: str):
    months = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]
    month, year = None, None
    for m in months:
        if m.lower() in text.lower():
            month = m
            break
    yr = re.search(r'\b(202\d|201\d)\b', text)
    if yr:
        year = yr.group(1)
    return month, year

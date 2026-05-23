"""
Shareable document links with move-tracking via lightweight content fingerprinting.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable

DB_PATH = str(Path(__file__).parent / "document_links.db")
FINGERPRINT_READ_BYTES = 2 * 1024 * 1024  # 2MB


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS document_links (
                token TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_mtime REAL,
                fingerprint TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by TEXT,
                last_resolved_at TEXT,
                last_accessed_at TEXT,
                access_count INTEGER DEFAULT 0
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_links_fingerprint ON document_links(fingerprint)")


def _norm(path: str) -> str:
    return str(Path(path).expanduser().resolve())


def _file_fingerprint(path: str) -> tuple[str, int, float]:
    st = os.stat(path)
    sha = hashlib.sha256()
    with open(path, "rb") as fh:
        sha.update(fh.read(FINGERPRINT_READ_BYTES))
    return sha.hexdigest(), int(st.st_size), float(st.st_mtime)


def create_or_get_link(file_path: str, created_by: str = "") -> dict:
    init_db()
    norm_path = _norm(file_path)
    if not os.path.exists(norm_path):
        raise FileNotFoundError(norm_path)
    fingerprint, file_size, file_mtime = _file_fingerprint(norm_path)
    file_name = os.path.basename(norm_path)

    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM document_links WHERE file_path = ?",
            (norm_path,),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE document_links
                   SET file_name = ?, file_size = ?, file_mtime = ?, fingerprint = ?
                 WHERE token = ?
                """,
                (file_name, file_size, file_mtime, fingerprint, row["token"]),
            )
            out = dict(row)
            out.update(
                {
                    "file_name": file_name,
                    "file_size": file_size,
                    "file_mtime": file_mtime,
                    "fingerprint": fingerprint,
                }
            )
            return out

        token = secrets.token_urlsafe(9)
        created_at = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            """
            INSERT INTO document_links
            (token, file_path, file_name, file_size, file_mtime, fingerprint, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (token, norm_path, file_name, file_size, file_mtime, fingerprint, created_at, created_by),
        )
        return {
            "token": token,
            "file_path": norm_path,
            "file_name": file_name,
            "file_size": file_size,
            "file_mtime": file_mtime,
            "fingerprint": fingerprint,
            "created_at": created_at,
            "created_by": created_by,
        }


def _candidate_roots(path_hint: str, extra_roots: Iterable[str] | None = None) -> list[str]:
    roots: list[str] = []
    p = Path(path_hint)
    roots.append(str(p.parent))
    try:
        roots.append(str(p.parent.parent))
    except Exception:
        pass
    for root in extra_roots or []:
        if root:
            roots.append(str(Path(root)))
    dedup: list[str] = []
    seen = set()
    for root in roots:
        nr = os.path.normcase(os.path.normpath(root))
        if nr in seen:
            continue
        seen.add(nr)
        dedup.append(root)
    return dedup


def _matches_record(path: str, *, size: int, fingerprint: str) -> bool:
    try:
        st = os.stat(path)
    except OSError:
        return False
    if int(st.st_size) != int(size):
        return False
    try:
        fp, _, _ = _file_fingerprint(path)
    except OSError:
        return False
    return fp == fingerprint


def _locate_moved_file(path_hint: str, *, size: int, fingerprint: str, extra_roots: Iterable[str] | None = None) -> str | None:
    for root in _candidate_roots(path_hint, extra_roots):
        if not os.path.isdir(root):
            continue
        for cur_root, _, files in os.walk(root):
            for name in files:
                cand = os.path.join(cur_root, name)
                if _matches_record(cand, size=size, fingerprint=fingerprint):
                    return _norm(cand)
    return None


def resolve_link(token: str, search_roots: Iterable[str] | None = None) -> dict | None:
    init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM document_links WHERE token = ?",
            (token,),
        ).fetchone()
        if not row:
            return None
        rec = dict(row)

        resolved_path = rec["file_path"]
        if not os.path.exists(resolved_path):
            found = _locate_moved_file(
                rec["file_path"],
                size=rec["file_size"],
                fingerprint=rec["fingerprint"],
                extra_roots=search_roots,
            )
            if found:
                resolved_path = found
                conn.execute(
                    "UPDATE document_links SET file_path = ?, file_name = ?, last_resolved_at = ? WHERE token = ?",
                    (
                        resolved_path,
                        os.path.basename(resolved_path),
                        datetime.now().isoformat(timespec="seconds"),
                        token,
                    ),
                )
                rec["file_path"] = resolved_path
                rec["file_name"] = os.path.basename(resolved_path)

        conn.execute(
            """
            UPDATE document_links
               SET last_accessed_at = ?, access_count = COALESCE(access_count, 0) + 1
             WHERE token = ?
            """,
            (datetime.now().isoformat(timespec="seconds"), token),
        )
        rec["exists"] = os.path.exists(resolved_path)
        rec["resolved_path"] = resolved_path
        return rec


def get_recent_links(limit: int = 50) -> list[dict]:
    init_db()
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM document_links
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]

"""More Tools (tasks T-30 to T-33).

Every tool is a function ``handler(ctx, data) -> dict`` registered in ``REGISTRY`` under its route
key. The function returns ``{"blocks": [...]}`` built with the helpers below, and the web app
renders those blocks with one shared component. See "Tool output blocks" in API_CONTRACT.md.

Rules every tool follows:
- Work from the caller's own loans (``loan_for``) and never read or write folders on disk.
- Nothing a user types or a loan holds is logged or stored by the tool itself.
- Any AI use goes through ``translate.py``-style helpers that redact first and use only the
  caller's own key.
"""
from __future__ import annotations

from typing import Any, Callable

from ..context import RequestContext
from ..errors import ApiError

Handler = Callable[[RequestContext, dict[str, Any]], dict[str, Any]]
REGISTRY: dict[str, Handler] = {}

Tone = str  # "good" | "warn" | "bad" | "info" | "neutral"


def tool(key: str) -> Callable[[Handler], Handler]:
    """Register a handler under its route key."""
    def register(handler: Handler) -> Handler:
        REGISTRY[key] = handler
        return handler
    return register


# ---------- output blocks ----------
def stats(*items: tuple[str, Any, Tone]) -> dict:
    return {"type": "stats", "items": [{"label": l, "value": v, "tone": t} for l, v, t in items]}


def listing(title: str, items: list[str], tone: Tone = "neutral") -> dict:
    return {"type": "list", "title": title, "tone": tone, "items": items}


def checklist(title: str, rows: list[tuple[str, bool]]) -> dict:
    return {"type": "checklist", "title": title, "rows": [{"label": l, "ok": ok} for l, ok in rows]}


def kv(title: str, rows: list[tuple[str, Any]]) -> dict:
    return {"type": "kv", "title": title, "rows": [{"label": l, "value": "" if v is None else str(v)} for l, v in rows]}


def text(title: str, body: str) -> dict:
    return {"type": "text", "title": title, "text": body}


def notice(tone: Tone, body: str, href: str = "", link_label: str = "") -> dict:
    return {"type": "notice", "tone": tone, "text": body, "href": href, "link_label": link_label}


def table(title: str, columns: list[str], rows: list[list[Any]]) -> dict:
    return {"type": "table", "title": title, "columns": columns,
            "rows": [["" if c is None else str(c) for c in row] for row in rows]}


def link(label: str, href: str) -> dict:
    return {"type": "link", "label": label, "href": href}


def result(*blocks: dict) -> dict:
    return {"blocks": list(blocks)}


# ---------- input helpers ----------
def loan_for(ctx: RequestContext, data: dict[str, Any]) -> dict:
    """The loan named by data["loan_id"], if the caller may see it (404 otherwise)."""
    from ..routers.loans import _find  # same visibility rule as the pipeline
    try:
        loan_id = int(data.get("loan_id"))
    except (TypeError, ValueError):
        raise ApiError(400, "choose_loan", "Choose a loan first.")
    return _find(loan_id, ctx)


def text_input(data: dict[str, Any], name: str, label: str, *, required: bool = True, limit: int = 20000) -> str:
    value = str(data.get(name) or "").strip()
    if required and not value:
        raise ApiError(400, "missing_input", f"{label} is required.")
    if len(value) > limit:
        raise ApiError(400, "too_long", f"{label} is too long.")
    return value


def load_tools() -> None:
    """Import the tool modules so they register themselves."""
    from . import quick  # noqa: F401

"""Who is calling the API, for the length of one request.

Engine modules (crm, cloud_client) check ``current()`` first and fall back to Streamlit's
session only when no API request is active (task T-03).
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class RequestContext:
    user_key: str          # Supabase user id; "" in sandbox
    email: str
    gemini_key: str        # the user's own key; "" if none. Never log it.
    sandbox: bool

    def __repr__(self) -> str:  # keep keys and emails out of logs and tracebacks
        return f"RequestContext(user_key={self.user_key!r}, sandbox={self.sandbox}, has_key={bool(self.gemini_key)})"


SANDBOX = RequestContext(user_key="", email="", gemini_key="", sandbox=True)

_current: ContextVar[RequestContext | None] = ContextVar("pa_request_context", default=None)


def current() -> RequestContext | None:
    """The active request's context, or None outside an API request."""
    return _current.get()


@contextmanager
def use(ctx: RequestContext) -> Iterator[RequestContext]:
    """Make ``ctx`` the active context inside the ``with`` block."""
    token = _current.set(ctx)
    try:
        yield ctx
    finally:
        _current.reset(token)

"""Turns an incoming request into a RequestContext (task T-04 completes this).

Skeleton behaviour: the sandbox header works; real sign-in returns 501 until T-04.
"""
from __future__ import annotations

from typing import AsyncIterator, Optional

from fastapi import Header

from . import context
from .errors import ApiError, NotBuilt


async def get_context(
    authorization: Optional[str] = Header(default=None),
    x_pa_sandbox: Optional[str] = Header(default=None),
) -> AsyncIterator[context.RequestContext]:
    """FastAPI dependency: yields the caller's context and keeps it active for the request."""
    if authorization and authorization.lower().startswith("bearer "):
        # T-04: validate the token with Supabase GET /auth/v1/user, cache 60 s,
        # user_key = user["id"], gemini_key = supabase_auth.load_user_gemini_key(...).
        raise NotBuilt("T-04")
    if x_pa_sandbox == "1":
        with context.use(context.SANDBOX) as ctx:
            yield ctx
        return
    raise ApiError(401, "not_signed_in", "Please sign in.")

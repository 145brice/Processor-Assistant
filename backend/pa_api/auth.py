"""Turns an incoming request into a RequestContext (task T-04 completes this).

Skeleton behaviour: the sandbox header works; real sign-in returns 501 until T-04.
"""
from __future__ import annotations

import os
import time
from typing import AsyncIterator, Optional

import httpx
from fastapi import Header

import supabase_auth

from . import context
from .errors import ApiError


_USER_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_SECONDS = 60.0


def _supabase_user(token: str) -> dict:
    now = time.monotonic()
    cached = _USER_CACHE.get(token)
    if cached and cached[0] > now:
        return cached[1]

    base_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    if not base_url or not anon_key:
        raise ApiError(401, "not_signed_in", "Please sign in.")
    try:
        response = httpx.get(
            f"{base_url}/auth/v1/user",
            headers={"apikey": anon_key, "Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
    except httpx.HTTPError:
        raise ApiError(401, "not_signed_in", "Please sign in.")
    if response.status_code != 200:
        raise ApiError(401, "not_signed_in", "Please sign in.")
    try:
        user = response.json()
    except ValueError:
        raise ApiError(401, "not_signed_in", "Please sign in.")
    if not isinstance(user, dict) or not user.get("id"):
        raise ApiError(401, "not_signed_in", "Please sign in.")
    _USER_CACHE[token] = (now + _CACHE_SECONDS, user)
    return user


async def get_context(
    authorization: Optional[str] = Header(default=None),
    x_pa_sandbox: Optional[str] = Header(default=None),
) -> AsyncIterator[context.RequestContext]:
    """FastAPI dependency: yields the caller's context and keeps it active for the request."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        if not token:
            raise ApiError(401, "not_signed_in", "Please sign in.")
        user = _supabase_user(token)
        user_key = str(user["id"])
        email = str(user.get("email") or "")
        gemini_key = supabase_auth.load_user_gemini_key(user_key, email)
        ctx = context.RequestContext(user_key, email, gemini_key, False)
        with context.use(ctx):
            yield ctx
        return
    if x_pa_sandbox == "1":
        with context.use(context.SANDBOX) as ctx:
            yield ctx
        return
    raise ApiError(401, "not_signed_in", "Please sign in.")

"""Account, AI key, usage and pricing endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from datetime import datetime, timezone
import os

import cloud_client
import product_config
import supabase_auth
import tiers

from .. import models as m
from ..auth import get_context
from ..context import RequestContext
from ..errors import ApiError, NotBuilt

router = APIRouter(prefix="/api", tags=["account"])


@router.get("/me", response_model=m.Me)
def get_me(ctx: RequestContext = Depends(get_context)) -> m.Me:
    if ctx.sandbox:
        return m.Me(
            user_key="", email="", name="Sandbox User", role="Processor", sandbox=True,
            terms_accepted=True,
            ai=m.AiKeyStatus(has_key=False, model=cloud_client.DEFAULT_MODELS["gemini"]),
            usage=None,
            features=m.Features(more_tools=product_config.advanced_tools_enabled(), owner=False,
                                setup_video_url=os.getenv("PA_GEMINI_SETUP_VIDEO") or None),
        )
    profile = supabase_auth.ensure_user_profile(ctx.user_key, email=ctx.email)
    quota = tiers.check_scan_quota(ctx.user_key, profile)
    name = str(profile.get("display_name") or ctx.email.split("@", 1)[0] or "User")
    role = str(profile.get("role") or "Processor")
    owners = {item.strip().lower() for item in os.getenv("PA_OWNER_ADMIN_EMAILS", "").split(",") if item.strip()}
    if ctx.email.lower() in owners:
        role = "Manager"
    return m.Me(
        user_key=ctx.user_key, email=ctx.email, name=name, role=role, sandbox=False,
        terms_accepted=bool(profile.get("terms_accepted_at")),
        ai=m.AiKeyStatus(has_key=bool(ctx.gemini_key), model=cloud_client.DEFAULT_MODELS["gemini"]),
        usage=m.UsageSummary(tier=quota["tier"], tier_name=quota["tier_name"], limit=quota["limit"],
                             used=quota["used"], remaining=quota["remaining"], free_beta=tiers.free_beta_mode()),
        features=m.Features(more_tools=product_config.advanced_tools_enabled(), owner=ctx.email.lower() in owners,
                            setup_video_url=os.getenv("PA_GEMINI_SETUP_VIDEO") or None),
    )


@router.post("/me/accept-terms", response_model=m.Ok)
def accept_terms(ctx: RequestContext = Depends(get_context)) -> m.Ok:
    if ctx.sandbox:
        raise ApiError(403, "sandbox_write", "Sign in to save changes.")
    supabase_auth.accept_terms(ctx.user_key, email=ctx.email)
    return m.Ok(ok=True)


@router.get("/ai-key", response_model=m.AiKeyStatus)
def get_ai_key(ctx: RequestContext = Depends(get_context)) -> m.AiKeyStatus:
    raise NotBuilt("T-15")


@router.put("/ai-key", response_model=m.AiKeyStatus)
def put_ai_key(body: m.AiKeyIn, ctx: RequestContext = Depends(get_context)) -> m.AiKeyStatus:
    # T-15: test with cloud_client.ping("gemini", body.key) BEFORE saving; save only on success.
    raise NotBuilt("T-15")


@router.post("/ai-key/test", response_model=m.TestResult)
def test_ai_key(ctx: RequestContext = Depends(get_context)) -> m.TestResult:
    raise NotBuilt("T-15")


@router.delete("/ai-key", response_model=m.AiKeyStatus)
def delete_ai_key(ctx: RequestContext = Depends(get_context)) -> m.AiKeyStatus:
    raise NotBuilt("T-15")


@router.get("/usage", response_model=m.UsageSummary)
def get_usage(ctx: RequestContext = Depends(get_context)) -> m.UsageSummary:
    raise NotBuilt("T-27")


@router.get("/pricing", response_model=m.Pricing)
def get_pricing(ctx: RequestContext = Depends(get_context)) -> m.Pricing:
    raise NotBuilt("T-27")

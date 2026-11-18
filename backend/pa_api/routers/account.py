"""Account, AI key, usage and pricing endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from .. import models as m
from ..auth import get_context
from ..context import RequestContext
from ..errors import NotBuilt

router = APIRouter(prefix="/api", tags=["account"])


@router.get("/me", response_model=m.Me)
def get_me(ctx: RequestContext = Depends(get_context)) -> m.Me:
    raise NotBuilt("T-13")


@router.post("/me/accept-terms", response_model=m.Ok)
def accept_terms(ctx: RequestContext = Depends(get_context)) -> m.Ok:
    raise NotBuilt("T-13")


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

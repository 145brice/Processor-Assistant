"""More Tools: one POST endpoint per tool route key.

Each tool lives in ``backend/pa_api/tools/`` and registers itself in ``REGISTRY``. A key that is not
registered answers 404. (Income Verifier, Auto Data Entry, Fraud Detector, Underwriting Tracker and
Team were removed on the owner's request because they never worked in the current app.)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from .. import models as m
from ..auth import get_context
from ..context import RequestContext
from ..errors import ApiError
from ..tools import REGISTRY, load_tools

router = APIRouter(prefix="/api/tools", tags=["tools"])

load_tools()


@router.post("/{tool}", response_model=m.ToolOut)
def run_tool(tool: str, body: m.ToolIn, ctx: RequestContext = Depends(get_context)) -> m.ToolOut:
    handler = REGISTRY.get(tool)
    if handler is None:
        raise ApiError(404, "unknown_tool", "That tool does not exist.")
    return m.ToolOut(output=handler(ctx, body.input))

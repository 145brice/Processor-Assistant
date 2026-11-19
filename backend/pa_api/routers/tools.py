"""More Tools: one POST endpoint per tool route key (tasks T-30 to T-33).

Each tool lives in ``backend/pa_api/tools/`` and registers itself in ``REGISTRY``. A tool that is
listed in ``TOOL_TASKS`` but not registered yet answers 501 naming the task that builds it.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from .. import models as m
from ..auth import get_context
from ..context import RequestContext
from ..errors import ApiError, NotBuilt
from ..tools import REGISTRY, load_tools

router = APIRouter(prefix="/api/tools", tags=["tools"])

TOOL_TASKS = {
    "snapshot": "T-30", "report_issue": "T-30", "missing_docs": "T-30", "doc_expiry": "T-30",
    "spanish_reply": "T-30",
    "income_verifier": "T-31", "auto_data_entry": "T-31", "credit_summary": "T-31",
    "dti_calculator": "T-31", "condition_clearer": "T-31", "compliance_checker": "T-31",
    "closing_package": "T-32", "pipeline_dashboard": "T-32", "guideline_checker": "T-32",
    "fraud_detector": "T-32", "multi_borrower": "T-32", "los_export": "T-32",
    "rate_lock_monitor": "T-32", "underwriting_tracker": "T-32", "document_classifier": "T-32",
    "escrow_calculator": "T-32",
    "team": "T-33",
}

load_tools()


@router.post("/{tool}", response_model=m.ToolOut)
def run_tool(tool: str, body: m.ToolIn, ctx: RequestContext = Depends(get_context)) -> m.ToolOut:
    handler = REGISTRY.get(tool)
    if handler is not None:
        return m.ToolOut(output=handler(ctx, body.input))
    task = TOOL_TASKS.get(tool)
    if task is None:
        raise ApiError(404, "unknown_tool", "That tool does not exist.")
    raise NotBuilt(task)

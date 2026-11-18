"""Pipeline and loan endpoints. Fixed paths are declared before /loans/{loan_id}."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, UploadFile

from .. import models as m
from ..auth import get_context
from ..context import RequestContext
from ..errors import NotBuilt

router = APIRouter(prefix="/api/loans", tags=["loans"])

Sort = Literal["newest", "borrower", "close", "lock", "loan_num", "status"]


@router.get("", response_model=m.LoanList)
def list_loans(
    status: Optional[m.LoanStatus] = None,
    q: Optional[str] = None,
    sort: Sort = "newest",
    mine: bool = False,
    ctx: RequestContext = Depends(get_context),
) -> m.LoanList:
    raise NotBuilt("T-24")


@router.post("", response_model=m.Loan)
def create_loan(body: m.LoanCreate, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    raise NotBuilt("T-24")


@router.get("/removed", response_model=m.RemovedLoans)
def removed_loans(ctx: RequestContext = Depends(get_context)) -> m.RemovedLoans:
    raise NotBuilt("T-24")


@router.post("/import", response_model=m.ImportResult)
async def import_loans(file: UploadFile = File(...), ctx: RequestContext = Depends(get_context)) -> m.ImportResult:
    raise NotBuilt("T-24")


@router.post("/from-scan", response_model=m.Loan)
def loan_from_scan(body: m.BatchIn, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    raise NotBuilt("T-23")


@router.get("/{loan_id}", response_model=m.Loan)
def get_loan(loan_id: int, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    raise NotBuilt("T-25")


@router.patch("/{loan_id}", response_model=m.Loan)
def update_loan(loan_id: int, body: m.LoanUpdate, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    raise NotBuilt("T-25")


@router.delete("/{loan_id}", response_model=m.Ok)
def delete_loan(loan_id: int, ctx: RequestContext = Depends(get_context)) -> m.Ok:
    raise NotBuilt("T-24")


@router.post("/{loan_id}/status", response_model=m.Loan)
def set_status(loan_id: int, body: m.StatusIn, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    raise NotBuilt("T-24")


@router.put("/{loan_id}/conditions", response_model=m.Loan)
def set_conditions(loan_id: int, body: m.ConditionsIn, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    raise NotBuilt("T-25")


@router.post("/{loan_id}/restore", response_model=m.Loan)
def restore_loan(loan_id: int, ctx: RequestContext = Depends(get_context)) -> m.Loan:
    raise NotBuilt("T-24")


@router.post("/{loan_id}/merge-scan", response_model=m.MergeResult)
def merge_scan(loan_id: int, body: m.BatchIn, ctx: RequestContext = Depends(get_context)) -> m.MergeResult:
    raise NotBuilt("T-23")


@router.get("/{loan_id}/activity", response_model=m.ActivityList)
def loan_activity(loan_id: int, ctx: RequestContext = Depends(get_context)) -> m.ActivityList:
    raise NotBuilt("T-26")

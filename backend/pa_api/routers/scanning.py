"""Upload, detection, scanning, saved scans and scan outputs."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from .. import models as m
from ..auth import get_context
from ..context import RequestContext
from ..errors import NotBuilt

router = APIRouter(prefix="/api", tags=["scanning"])

MAX_UPLOAD_BYTES = 40 * 1024 * 1024  # same limit as production (.streamlit/config.toml)


@router.post("/scan/detect", response_model=m.DetectResponse)
async def detect(files: list[UploadFile] = File(...), ctx: RequestContext = Depends(get_context)) -> m.DetectResponse:
    # T-20: read each file in memory (reject > MAX_UPLOAD_BYTES with 413), ai_engine.detect_doc_type.
    raise NotBuilt("T-20")


@router.post("/scan", response_model=m.ScanResponse)
async def scan(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    ctx: RequestContext = Depends(get_context),
) -> m.ScanResponse:
    # T-21: quota -> ai_engine.process_document(bytes, doc_type, user_approved_cloud=...)
    # -> normalize conditions -> doc_verify._match_borrower -> billing.log_scan -> history.
    # Never pass the PDF bytes to any AI function (RULES.md section 1).
    raise NotBuilt("T-21")


@router.get("/scans", response_model=m.SavedScans)
def list_scans(ctx: RequestContext = Depends(get_context)) -> m.SavedScans:
    raise NotBuilt("T-27")


@router.delete("/scans/{scan_id}", response_model=m.Ok)
def delete_scan(scan_id: str, ctx: RequestContext = Depends(get_context)) -> m.Ok:
    raise NotBuilt("T-27")


@router.post("/outputs/email-drafts", response_model=m.EmailDrafts)
def email_drafts(body: m.BatchIn, ctx: RequestContext = Depends(get_context)) -> m.EmailDrafts:
    raise NotBuilt("T-22")


@router.post("/outputs/csv")
def export_csv(body: m.BatchIn, ctx: RequestContext = Depends(get_context)):
    raise NotBuilt("T-22")


@router.post("/outputs/pdf")
def export_pdf(body: m.BatchIn, ctx: RequestContext = Depends(get_context)):
    raise NotBuilt("T-22")

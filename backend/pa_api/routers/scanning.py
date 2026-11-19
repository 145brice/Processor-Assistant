"""Upload, detection, scanning, saved scans and scan outputs."""
from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

import scan_history_store
import scan_outputs

from .. import detection, scan_service
from .. import models as m
from ..auth import get_context
from ..context import RequestContext
from ..errors import ApiError, NotBuilt

router = APIRouter(prefix="/api", tags=["scanning"])

MAX_UPLOAD_BYTES = 40 * 1024 * 1024  # same limit as production (.streamlit/config.toml)


async def read_pdf(upload: UploadFile) -> bytes:
    """Read one uploaded PDF into memory. Never written to disk, never logged.

    Over MAX_UPLOAD_BYTES -> 413; not a PDF -> 400. Messages name the file the user chose,
    which is theirs to see, and nothing from inside it.
    """
    data = await upload.read(MAX_UPLOAD_BYTES + 1)
    name = upload.filename or "file"
    if len(data) > MAX_UPLOAD_BYTES:
        raise ApiError(413, "file_too_large", f"{name} is over the 40 MB limit.")
    if not data.lstrip()[:5].startswith(b"%PDF"):
        raise ApiError(400, "not_a_pdf", f"{name} is not a PDF. Upload PDF files only.")
    return data


@router.post("/scan/detect", response_model=m.DetectResponse)
async def detect(files: list[UploadFile] = File(...), ctx: RequestContext = Depends(get_context)) -> m.DetectResponse:
    out: list[m.DetectedFile] = []
    for upload in files:
        data = await read_pdf(upload)
        name = upload.filename or "document.pdf"
        found = await run_in_threadpool(detection.detect, name, data)
        out.append(m.DetectedFile(name=name, size_bytes=len(data), **found))
        del data
    return m.DetectResponse(files=out)


@router.post("/scan", response_model=m.ScanResponse)
async def scan(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    ctx: RequestContext = Depends(get_context),
) -> m.ScanResponse:
    # Never pass the PDF bytes to any AI function (RULES.md section 1): scan_service hands them
    # only to ai_engine.process_document, which extracts text locally.
    if doc_type not in detection.DOC_TYPES or doc_type == "Unknown":
        raise ApiError(400, "choose_doc_type", "Choose a document type before scanning this file.")
    data = await read_pdf(file)
    name = file.filename or "document.pdf"
    response = await run_in_threadpool(scan_service.run_scan, ctx, name, data, doc_type)
    del data
    return response


@router.get("/scans", response_model=m.SavedScans)
def list_scans(ctx: RequestContext = Depends(get_context)) -> m.SavedScans:
    if ctx.sandbox:
        return m.SavedScans(items=[])
    loaded = scan_history_store.load(ctx.user_key)
    if not loaded.get("ok"):
        raise ApiError(503, "history_unavailable", loaded.get("error", "Could not load saved scans."))
    items = []
    for entry in loaded.get("items", []):
        if entry.get("user_key") != ctx.user_key:
            continue
        try:
            saved_at = datetime.fromtimestamp(float(entry["ts"]), tz=timezone.utc).isoformat().replace("+00:00", "Z")
            batch = scan_service.saved_batch_to_contract(entry["batch"])
            items.append(m.SavedScan(id=str(entry["id"]), saved_at=saved_at, batch=batch))
        except (KeyError, TypeError, ValueError):
            continue
    items.sort(key=lambda item: item.saved_at, reverse=True)
    return m.SavedScans(items=items)


@router.delete("/scans/{scan_id}", response_model=m.Ok)
def delete_scan(scan_id: str, ctx: RequestContext = Depends(get_context)) -> m.Ok:
    if ctx.sandbox:
        raise ApiError(403, "sandbox_write", "Sign in to save changes.")
    loaded = scan_history_store.load(ctx.user_key)
    if not loaded.get("ok"):
        raise ApiError(503, "history_unavailable", loaded.get("error", "Could not load saved scans."))
    items = loaded.get("items", [])
    kept = [item for item in items if str(item.get("id")) != scan_id]
    if len(kept) == len(items):
        raise ApiError(404, "not_found", "Saved scan not found.")
    saved = scan_history_store.save(ctx.user_key, kept, ctx.email)
    if not saved.get("ok"):
        raise ApiError(503, "save_failed", "Could not delete the saved scan. Please try again.")
    return m.Ok(ok=True)


# ---------- outputs (T-22): local text and files built by scan_outputs; no AI, nothing stored ----------
def _split_subject(draft: str) -> m.EmailDraft:
    """scan_outputs drafts start with 'Subject: ...' then a blank line."""
    first, _, rest = draft.partition("\n\n")
    if first.lower().startswith("subject:"):
        return m.EmailDraft(subject=first[len("subject:"):].strip(), body=rest.strip())
    return m.EmailDraft(subject="", body=draft.strip())


@router.post("/outputs/email-drafts", response_model=m.EmailDrafts)
def email_drafts(body: m.BatchIn, ctx: RequestContext = Depends(get_context)) -> m.EmailDrafts:
    borrower_email, officer_email = scan_outputs.email_drafts(body.batch.model_dump())
    return m.EmailDrafts(borrower_needs_list=_split_subject(borrower_email),
                         loan_officer_update=_split_subject(officer_email))


@router.post("/outputs/csv")
def export_csv(body: m.BatchIn, ctx: RequestContext = Depends(get_context)) -> Response:
    data = scan_outputs.csv_bytes(body.batch.model_dump())
    return Response(content=data, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="loan-scan.csv"'})


@router.post("/outputs/pdf")
def export_pdf(body: m.BatchIn, ctx: RequestContext = Depends(get_context)) -> Response:
    data = scan_outputs.pdf_bytes(body.batch.model_dump())
    return Response(content=data, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="loan-scan.pdf"'})

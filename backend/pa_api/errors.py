"""Error responses in the contract's shape: {"error": {"code", "message"}}."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


class NotBuilt(ApiError):
    """Raised by skeleton endpoints. The message names the task that builds it."""

    def __init__(self, task: str):
        super().__init__(501, "not_built", f"Not built yet: see {task} in docs/nextjs-rebuild/TASKS.md")


def _body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(_body(exc.code, exc.message), status_code=exc.status)

    @app.exception_handler(HTTPException)
    async def _http_error(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(_body(f"http_{exc.status_code}", str(exc.detail)), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Field locations only; never echo submitted values (they may contain personal data).
        fields = ", ".join(".".join(str(p) for p in e.get("loc", [])) for e in exc.errors())
        return JSONResponse(_body("validation", f"Invalid or missing fields: {fields}"), status_code=422)

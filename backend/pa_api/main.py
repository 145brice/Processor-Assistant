"""FastAPI entry point: uvicorn backend.pa_api.main:app --port 8600"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__, errors
from .models import Health
from .routers import account, loans, scanning, tools

app = FastAPI(title="Processor Assistant API", version=__version__)
errors.install(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("PA_WEB_ORIGIN", "http://localhost:3000").split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-PA-Sandbox"],
)

for _router in (account.router, scanning.router, loans.router, tools.router):
    app.include_router(_router)


@app.get("/api/health", response_model=Health, tags=["health"])
def health() -> Health:
    return Health(ok=True, version=__version__)

import base64
import calendar
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

DB_PATH = os.getenv("PROCESSOR_API_DB", "processor_api.db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DEFAULT_CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")

app = FastAPI(
    title="Processor Language API",
    version="1.0.0",
    description="REST API for parse, translate, and email drafting features.",
)


class ParseDocumentRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    pdf_base64: str = Field(..., min_length=20)
    filename: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranslateConditionRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    condition_text: str = Field(..., min_length=3)
    audience: str = Field(..., pattern="^(borrower|appraiser|realtor)$")


class GenerateEmailRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    conditions: List[str] = Field(..., min_length=1)
    recipient_type: str = Field(..., min_length=2)
    language: str = Field(..., pattern="^(english|spanish)$")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def month_bounds(dt: datetime) -> tuple[str, str]:
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    end = dt.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
    return start.isoformat(), end.isoformat()


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            plan TEXT NOT NULL CHECK (plan IN ('59', '199')),
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            key_hash TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
        """
    )
    conn.commit()
    conn.close()


@app.on_event("startup")
def startup() -> None:
    init_db()


def get_customer_for_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> sqlite3.Row:
    key_hash = hash_api_key(x_api_key.strip())
    conn = get_conn()
    row = conn.execute(
        """
        SELECT c.id, c.name, c.plan
        FROM api_keys k
        JOIN customers c ON c.id = k.customer_id
        WHERE k.key_hash = ? AND k.is_active = 1
        """,
        (key_hash,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return row


def enforce_and_record_usage(customer_id: str, endpoint: str, plan: str) -> Dict[str, Any]:
    now = utc_now()
    month_start, month_end = month_bounds(now)
    conn = get_conn()
    used = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM usage_events
        WHERE customer_id = ? AND created_at >= ? AND created_at <= ?
        """,
        (customer_id, month_start, month_end),
    ).fetchone()["c"]

    limit = 50 if plan == "59" else None
    if limit is not None and used >= limit:
        conn.close()
        raise HTTPException(
            status_code=429,
            detail={
                "error": "quota_exceeded",
                "plan": plan,
                "monthly_limit": limit,
                "used": used,
            },
        )

    conn.execute(
        "INSERT INTO usage_events (customer_id, endpoint, created_at) VALUES (?, ?, ?)",
        (customer_id, endpoint, now.isoformat()),
    )
    conn.commit()
    conn.close()

    return {
        "plan": plan,
        "monthly_limit": limit,
        "monthly_used": used + 1,
        "period_start": month_start,
        "period_end": month_end,
    }


async def call_gemini_extract_conditions(pdf_bytes: bytes) -> Dict[str, Any]:
    if not GEMINI_API_KEY:
        return {
            "conditions": [],
            "confidence": 0.0,
            "notes": "GEMINI_API_KEY is not configured",
        }

    encoded = base64.b64encode(pdf_bytes).decode("utf-8")
    prompt = (
        "Extract underwriting/approval conditions from this mortgage document. "
        "Return strict JSON: {\"conditions\": [string], \"confidence\": number, \"notes\": string}."
    )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{DEFAULT_GEMINI_MODEL}:generateContent"
        f"?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "application/pdf", "data": encoded}},
                ]
            }
        ],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload)
    if resp.status_code >= 400:
        return {"conditions": [], "confidence": 0.0, "notes": f"Gemini error: {resp.text[:200]}"}

    data = resp.json()
    text = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "{}")
    )
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"conditions": [], "confidence": 0.0, "notes": "Gemini returned non-JSON content"}


async def call_claude_translate(condition_text: str, audience: str) -> Dict[str, Any]:
    if not ANTHROPIC_API_KEY:
        return {
            "rewritten_condition": condition_text,
            "audience": audience,
            "readability": "unknown",
            "notes": "ANTHROPIC_API_KEY is not configured",
        }

    system = "You rewrite mortgage conditions so non-underwriters can understand them."
    user = (
        f"Rewrite this condition for a {audience}. Return strict JSON with keys "
        f"rewritten_condition, audience, readability, notes.\nCondition: {condition_text}"
    )
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": DEFAULT_CLAUDE_MODEL,
        "max_tokens": 500,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
    if resp.status_code >= 400:
        return {
            "rewritten_condition": condition_text,
            "audience": audience,
            "readability": "unknown",
            "notes": f"Claude error: {resp.text[:200]}",
        }

    content = resp.json().get("content", [])
    text = content[0].get("text", "{}") if content else "{}"
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "rewritten_condition": text.strip() or condition_text,
            "audience": audience,
            "readability": "unknown",
            "notes": "Claude returned non-JSON content",
        }


def local_email_draft(conditions: List[str], recipient_type: str, language: str) -> Dict[str, str]:
    if language == "spanish":
        subject = "Condiciones pendientes para su prestamo"
        intro = f"Hola,\n\nComparto las condiciones pendientes para {recipient_type}:"
        close = "\n\nGracias,\nEquipo de Procesamiento"
    else:
        subject = "Outstanding loan conditions"
        intro = f"Hello,\n\nHere are the outstanding conditions for the {recipient_type}:"
        close = "\n\nThank you,\nProcessing Team"

    bullets = "\n".join([f"- {c}" for c in conditions])
    body = f"{intro}\n{bullets}{close}"
    return {"subject": subject, "body": body, "language": language}


@app.post("/api/parse-document")
async def parse_document(req: ParseDocumentRequest, customer: sqlite3.Row = Depends(get_customer_for_api_key)) -> Dict[str, Any]:
    if req.customer_id != customer["id"]:
        raise HTTPException(status_code=403, detail="customer_id does not match API key owner")

    usage = enforce_and_record_usage(customer["id"], "/api/parse-document", customer["plan"])
    try:
        pdf_bytes = base64.b64decode(req.pdf_base64)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Invalid pdf_base64: {exc}") from exc

    result = await call_gemini_extract_conditions(pdf_bytes)
    return {"ok": True, "endpoint": "parse-document", "usage": usage, "data": result}


@app.post("/api/translate-condition")
async def translate_condition(req: TranslateConditionRequest, customer: sqlite3.Row = Depends(get_customer_for_api_key)) -> Dict[str, Any]:
    if req.customer_id != customer["id"]:
        raise HTTPException(status_code=403, detail="customer_id does not match API key owner")

    usage = enforce_and_record_usage(customer["id"], "/api/translate-condition", customer["plan"])
    result = await call_claude_translate(req.condition_text, req.audience)
    return {"ok": True, "endpoint": "translate-condition", "usage": usage, "data": result}


@app.post("/api/generate-email")
async def generate_email(req: GenerateEmailRequest, customer: sqlite3.Row = Depends(get_customer_for_api_key)) -> Dict[str, Any]:
    if req.customer_id != customer["id"]:
        raise HTTPException(status_code=403, detail="customer_id does not match API key owner")

    usage = enforce_and_record_usage(customer["id"], "/api/generate-email", customer["plan"])
    draft = local_email_draft(req.conditions, req.recipient_type, req.language)
    return {"ok": True, "endpoint": "generate-email", "usage": usage, "data": draft}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT c.id, c.name, c.plan, COUNT(u.id) AS monthly_calls
        FROM customers c
        LEFT JOIN usage_events u ON u.customer_id = c.id
          AND u.created_at >= ?
          AND u.created_at <= ?
        GROUP BY c.id, c.name, c.plan
        ORDER BY monthly_calls DESC, c.name ASC
        """,
        month_bounds(utc_now()),
    ).fetchall()
    conn.close()

    row_html = "".join(
        [
            "<tr>"
            f"<td>{r['id']}</td><td>{r['name']}</td><td>${r['plan']}/mo</td><td>{r['monthly_calls']}</td>"
            "</tr>"
            for r in rows
        ]
    )

    return f"""
    <html>
      <head>
        <title>Processor API Dashboard</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
          th {{ background: #f4f4f4; }}
        </style>
      </head>
      <body>
        <h1>Processor API Usage Dashboard</h1>
        <p>Billing month: {utc_now().strftime('%Y-%m')}</p>
        <table>
          <thead><tr><th>Customer ID</th><th>Name</th><th>Plan</th><th>Monthly Calls</th></tr></thead>
          <tbody>{row_html or '<tr><td colspan="4">No customers yet</td></tr>'}</tbody>
        </table>
        <p>Swagger Docs: <a href="/docs">/docs</a></p>
      </body>
    </html>
    """


class CreateCustomerRequest(BaseModel):
    customer_id: str
    name: str
    plan: str = Field(..., pattern="^(59|199)$")
    api_key: str = Field(..., min_length=12)


@app.post("/admin/customers")
def create_customer(req: CreateCustomerRequest) -> Dict[str, Any]:
    now = utc_now().isoformat()
    key_hash = hash_api_key(req.api_key)
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO customers (id, name, plan, created_at) VALUES (?, ?, ?, ?)",
            (req.customer_id, req.name, req.plan, now),
        )
        conn.execute(
            "INSERT INTO api_keys (key_hash, customer_id, is_active, created_at) VALUES (?, ?, 1, ?)",
            (key_hash, req.customer_id, now),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail=f"Customer or key already exists: {exc}") from exc
    finally:
        conn.close()

    return {"ok": True, "customer_id": req.customer_id, "plan": req.plan}

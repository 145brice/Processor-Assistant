"""API models. Must match docs/nextjs-rebuild/API_CONTRACT.md and web/src/lib/types.ts."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

ConditionStatus = Literal["Needed", "Requested", "Important", "Ready to Clear", "Cleared"]
LoanStatus = Literal["Pending", "Requested", "Cleared", "Overdue", "Closed"]
DocType = Literal[
    "Approval Letter", "Loan Estimate (LE)", "1003 Application", "Purchase Contract",
    "Credit Report", "Bank Statement", "Change of Circumstance (COC)", "Broker Package (BP)",
    "Pay Stub", "W-2", "1099", "Tax Return", "Appraisal", "Title Commitment",
    "Hazard Insurance", "Mortgage Statement", "VA Certificate of Eligibility", "DD-214",
    "Government ID", "Unknown",
]
TierKey = Literal["free", "starter", "pro", "unlimited"]


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


# ---------- shared ----------
class Condition(BaseModel):
    num: int
    desc: str
    party: str
    status: ConditionStatus
    section: Optional[str] = None


class Contact(BaseModel):
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


# ---------- account ----------
class KeyCheck(BaseModel):
    ok: bool
    message: str
    checked_at: str


class AiKeyStatus(BaseModel):
    has_key: bool
    provider: Literal["gemini"] = "gemini"
    model: str
    last_check: Optional[KeyCheck] = None


class AiKeyIn(BaseModel):
    key: str = Field(min_length=1)


class TestResult(BaseModel):
    ok: bool
    message: str


class UsageSummary(BaseModel):
    tier: TierKey
    tier_name: str
    limit: Optional[int]
    used: int
    remaining: Optional[int]
    free_beta: bool


class Features(BaseModel):
    more_tools: bool
    owner: bool
    setup_video_url: Optional[str] = None


class Me(BaseModel):
    user_key: str
    email: str
    name: str
    role: str
    sandbox: bool
    terms_accepted: bool
    ai: AiKeyStatus
    usage: Optional[UsageSummary]
    features: Features


class Ok(BaseModel):
    ok: bool = True


# ---------- scanning ----------
class DetectedFile(BaseModel):
    name: str
    size_bytes: int
    detected_type: DocType
    confidence: Literal["High", "Medium", "Low"]


class DetectResponse(BaseModel):
    files: list[DetectedFile]


class ScanResult(BaseModel):
    success: bool
    doc_type: DocType
    conditions: list[Condition] = []
    extracted_data: dict[str, Any] = {}
    contacts: dict[str, Contact] = {}
    risks: str = ""
    image_only: bool = False
    ai_used: bool = False
    ai_note: str = ""
    error: str = ""


class LoanMatch(BaseModel):
    loan_id: Optional[int] = None
    loan_num: str = ""
    borrower: str = ""
    confidence: int = 0
    suggestion: Literal["match", "possible", "unknown"] = "unknown"


class ScanBatch(BaseModel):
    file: str
    type: DocType
    result: ScanResult
    loan_match: LoanMatch


class ScanResponse(ScanBatch):
    usage: Optional[UsageSummary] = None


class SavedScan(BaseModel):
    id: str
    saved_at: str
    batch: ScanBatch


class SavedScans(BaseModel):
    items: list[SavedScan]


class BatchIn(BaseModel):
    batch: ScanBatch


# ---------- loans ----------
class LoanSummary(BaseModel):
    id: int
    loan_num: str
    borrower: str
    status: LoanStatus
    closing_date: str = ""
    lock_expiry: str = ""
    lock_expired: bool = False
    missing_docs: str = ""
    assigned_to: str = ""
    progress_percent: int = 0
    contacts_line: str = ""
    updated: str = ""


class LoanDocument(BaseModel):
    filename: str
    doc_type: str
    scanned_at: str


class Loan(LoanSummary):
    property_address: str = ""
    lender: str = ""
    loan_amount: str = ""
    purchase_price: str = ""
    loan_type: str = ""
    due_date: str = ""
    loan_officer: str = ""
    loan_processor: str = ""
    notes: str = ""
    contacts: dict[str, Contact] = {}
    conditions: list[Condition] = []
    documents: list[LoanDocument] = []


class StatusCounts(BaseModel):
    all: int
    pending: int
    requested: int
    cleared: int
    overdue: int
    closed: int


class LoanList(BaseModel):
    loans: list[LoanSummary]
    counts: StatusCounts


class RemovedLoans(BaseModel):
    loans: list[LoanSummary]
    retention_days: int


class LoanCreate(BaseModel):
    loan_num: str
    borrower: str
    status: LoanStatus
    due_date: Optional[str] = None
    closing_date: Optional[str] = None
    lock_expiry: Optional[str] = None
    missing_docs: Optional[str] = None
    assigned_to: Optional[str] = None
    property_address: Optional[str] = None


class LoanUpdate(BaseModel):
    loan_num: Optional[str] = None
    borrower: Optional[str] = None
    status: Optional[LoanStatus] = None
    closing_date: Optional[str] = None
    lock_expiry: Optional[str] = None
    missing_docs: Optional[str] = None
    assigned_to: Optional[str] = None
    property_address: Optional[str] = None
    lender: Optional[str] = None
    loan_amount: Optional[str] = None
    purchase_price: Optional[str] = None
    loan_type: Optional[str] = None
    due_date: Optional[str] = None
    loan_officer: Optional[str] = None
    loan_processor: Optional[str] = None
    notes: Optional[str] = None
    contacts: Optional[dict[str, Contact]] = None
    conditions: Optional[list[Condition]] = None
    documents: Optional[list[LoanDocument]] = None


class StatusIn(BaseModel):
    status: LoanStatus


class ConditionsIn(BaseModel):
    conditions: list[Condition]


class MergeResult(BaseModel):
    loan: Loan
    added_conditions: int


class Activity(BaseModel):
    at: str
    action: str
    detail: str
    user: str


class ActivityList(BaseModel):
    items: list[Activity]


class ImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


# ---------- outputs ----------
class EmailDraft(BaseModel):
    subject: str
    body: str


class EmailDrafts(BaseModel):
    borrower_needs_list: EmailDraft
    loan_officer_update: EmailDraft


# ---------- pricing ----------
class Tier(BaseModel):
    key: str
    name: str
    price: float
    scan_limit: Optional[int]
    payment_link: Optional[str]


class Pricing(BaseModel):
    tiers: list[Tier]
    beta_offer: str
    free_beta: bool


class ToolIn(BaseModel):
    input: dict[str, Any] = {}


class ToolOut(BaseModel):
    output: dict[str, Any]


class Health(BaseModel):
    ok: bool
    version: str

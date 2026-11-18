# API contract

The single source of truth for frontend and backend. `web/src/lib/types.ts` and
`backend/pa_api/models.py` must match this file field for field. Change this file first if a
change is needed, then both sides in the same task.

## Conventions

- Base path `/api`. JSON in and out unless noted. Field names are `snake_case` on both sides.
- Every request except `/api/health` needs `Authorization: Bearer <Supabase access token>` or,
  for the demo, header `X-PA-Sandbox: 1`.
- Errors always look like `{"error": {"code": "string", "message": "string"}}` with these
  status codes: `400` bad input, `401` not signed in, `402` monthly scan limit reached, `403`
  not allowed (owner-only or sandbox write), `404` not found, `413` file over 40 MB, `422`
  validation, `500` server misconfigured or unexpected error, `501` not built yet (skeleton
  stubs).
- Messages are plain English for the user and never contain document content.
- Dates are ISO strings (`2026-11-17` or `2026-11-17T21:36:03Z`). Money stays a string as
  stored today (`"$325,000"`).

## Types

```ts
// ---------- shared ----------
type ConditionStatus = "Needed" | "Requested" | "Important" | "Ready to Clear" | "Cleared";
type LoanStatus = "Pending" | "Requested" | "Cleared" | "Overdue" | "Closed";   // crm.STATUS_OPTIONS
type DocType =
  | "Approval Letter" | "Loan Estimate (LE)" | "1003 Application" | "Purchase Contract"
  | "Credit Report" | "Bank Statement" | "Change of Circumstance (COC)" | "Broker Package (BP)"
  | "Pay Stub" | "W-2" | "1099" | "Tax Return" | "Appraisal" | "Title Commitment"
  | "Hazard Insurance" | "Mortgage Statement" | "VA Certificate of Eligibility" | "DD-214"
  | "Government ID" | "Unknown";

interface Condition {
  num: number;
  desc: string;
  party: string;              // Borrower, Title, Underwriter, Insurance, Closer, Appraiser, Employer, Realtor, Seller
  status: ConditionStatus;
  section?: string;           // PTD, PTF, AC, BOR... when known
}

interface Contact { name: string; company?: string; phone?: string; email?: string; role?: string; }

// ---------- account ----------
interface AiKeyStatus {
  has_key: boolean;
  provider: "gemini";
  model: string;              // e.g. "gemini-2.5-flash"
  last_check: { ok: boolean; message: string; checked_at: string } | null;
}

interface UsageSummary {
  tier: "free" | "starter" | "pro" | "unlimited";
  tier_name: string;          // "Beta — Free" during free beta
  limit: number | null;       // null = unlimited
  used: number;
  remaining: number | null;
  free_beta: boolean;
}

interface Me {
  user_key: string;           // Supabase user id; "" in sandbox
  email: string;
  name: string;
  role: string;               // "Processor", "Manager", ...
  sandbox: boolean;
  terms_accepted: boolean;
  ai: AiKeyStatus;
  usage: UsageSummary | null; // null in sandbox
  features: { more_tools: boolean; owner: boolean; setup_video_url: string | null };
}

// ---------- scanning ----------
interface DetectedFile {
  name: string;
  size_bytes: number;
  detected_type: DocType;
  confidence: "High" | "Medium" | "Low";
}

interface ScanResult {
  success: boolean;
  doc_type: DocType;
  conditions: Condition[];               // normalized; [] when none
  extracted_data: Record<string, unknown>;
  contacts: Record<string, Contact>;     // key = role ("borrower", "listing_agent", "title", ...)
  risks: string;
  image_only: boolean;                   // scanned image with no readable text
  ai_used: boolean;                      // AI enhanced this result (redacted text only)
  ai_note: string;                       // short, user-safe note, e.g. "Enhanced with Gemini" or "Local extraction only"
  error: string;                         // "" when success
}

interface LoanMatch {
  loan_id: number | null;
  loan_num: string;
  borrower: string;
  confidence: number;                    // 0-100
  suggestion: "match" | "possible" | "unknown";
}

interface ScanBatch {
  file: string;
  type: DocType;
  result: ScanResult;
  loan_match: LoanMatch;
}

interface SavedScan { id: string; saved_at: string; batch: ScanBatch; }

// ---------- loans ----------
interface LoanSummary {
  id: number;
  loan_num: string;
  borrower: string;
  status: LoanStatus;
  closing_date: string;
  lock_expiry: string;
  lock_expired: boolean;
  missing_docs: string;
  assigned_to: string;
  progress_percent: number;              // share of conditions Cleared
  contacts_line: string;                 // "Seller: ... | L.Agent: ... | Title: ..."
  updated: string;
}

interface Loan extends LoanSummary {
  property_address: string;
  lender: string;
  loan_amount: string;
  purchase_price: string;
  loan_type: string;
  due_date: string;
  loan_officer: string;
  loan_processor: string;
  notes: string;
  contacts: Record<string, Contact>;
  conditions: Condition[];
  documents: { filename: string; doc_type: string; scanned_at: string }[];
}

interface StatusCounts { all: number; pending: number; requested: number; cleared: number; overdue: number; closed: number; }

interface LoanCreate {
  loan_num: string; borrower: string; status: LoanStatus;
  due_date?: string; closing_date?: string; lock_expiry?: string;
  missing_docs?: string; assigned_to?: string; property_address?: string;
}
type LoanUpdate = Partial<Omit<Loan, "id" | "updated" | "progress_percent" | "contacts_line" | "lock_expired">>;

interface Activity { at: string; action: string; detail: string; user: string; }

// ---------- outputs ----------
interface EmailDraft { subject: string; body: string; }
interface EmailDrafts { borrower_needs_list: EmailDraft; loan_officer_update: EmailDraft; }

// ---------- pricing ----------
interface Tier { key: string; name: string; price: number; scan_limit: number | null; payment_link: string | null; }
```

## Endpoints

| Method and path | Request | Response | Engine call | Task |
|---|---|---|---|---|
| `GET /api/health` | none | `{ok: true, version: string}` | none | done |
| `GET /api/me` | none | `Me` | `supabase_auth.ensure_user_profile`, `load_user_gemini_key`, `tiers.check_scan_quota` | T-13 |
| `POST /api/me/accept-terms` | none | `{ok: true}` | `supabase_auth.accept_terms` | T-13 |
| `GET /api/ai-key` | none | `AiKeyStatus` | `supabase_auth.load_user_gemini_key` (never return the key) | T-15 |
| `PUT /api/ai-key` | `{key: string}` | `AiKeyStatus` | test with `cloud_client.ping("gemini", key)` first; save with `supabase_auth.save_user_gemini_key` **only if the test passes**; on failure `400` with a plain reason (bad key, billing not enabled, quota) | T-15 |
| `POST /api/ai-key/test` | none | `{ok: boolean, message: string}` | `cloud_client.ping` with the saved key | T-15 |
| `DELETE /api/ai-key` | none | `AiKeyStatus` | save empty key | T-15 |
| `POST /api/scan/detect` | multipart `files[]` (PDF, each ≤ 40 MB) | `{files: DetectedFile[]}` | `ai_engine.detect_doc_type` | T-20 |
| `POST /api/scan` | multipart `file`, `doc_type` | `ScanBatch & {usage: UsageSummary \| null}` | quota check, `ai_engine.process_document(bytes, doc_type, user_approved_cloud=ctx has key and doc_type in {"Approval Letter","Purchase Contract"})`, normalize conditions, `doc_verify._match_borrower`, `billing.log_scan`, save to history | T-21 |
| `GET /api/scans` | none | `{items: SavedScan[]}` | `scan_history_store.load` | T-27 |
| `DELETE /api/scans/{id}` | none | `{ok: true}` | `scan_history_store.save` without the item | T-27 |
| `POST /api/outputs/email-drafts` | `{batch: ScanBatch}` | `EmailDrafts` | `scan_outputs.email_drafts` | T-22 |
| `POST /api/outputs/csv` | `{batch: ScanBatch}` | `text/csv` file | `scan_outputs.csv_bytes` | T-22 |
| `POST /api/outputs/pdf` | `{batch: ScanBatch}` | `application/pdf` file | `scan_outputs.pdf_bytes` | T-22 |
| `GET /api/loans` | query `status?`, `q?`, `sort?` (`newest`,`borrower`,`close`,`lock`,`loan_num`,`status`), `mine?` | `{loans: LoanSummary[], counts: StatusCounts}` | `crm.get_all_loans` | T-24 |
| `POST /api/loans` | `LoanCreate` | `Loan` | `crm.add_loan` | T-24 |
| `GET /api/loans/{id}` | none | `Loan` | `crm.get_loan` | T-25 |
| `PATCH /api/loans/{id}` | `LoanUpdate` | `Loan` | `crm.update_loan` | T-25 |
| `POST /api/loans/{id}/status` | `{status: LoanStatus}` | `Loan` | `crm.set_status` | T-24 |
| `PUT /api/loans/{id}/conditions` | `{conditions: Condition[]}` | `Loan` | `crm.update_loan(conditions=...)` | T-25 |
| `DELETE /api/loans/{id}` | none | `{ok: true}` (moves to removed) | `crm.delete_loan` | T-24 |
| `GET /api/loans/removed` | none | `{loans: LoanSummary[], retention_days: number}` | `crm.get_trash`, `get_retention_days` | T-24 |
| `POST /api/loans/{id}/restore` | none | `Loan` | `crm.restore_loan` | T-24 |
| `POST /api/loans/from-scan` | `{batch: ScanBatch}` | `Loan` | `crm.add_loan` + `attach_document` (same fields the scanner's "Start New Loan" fills) | T-23 |
| `POST /api/loans/{id}/merge-scan` | `{batch: ScanBatch}` | `{loan: Loan, added_conditions: number}` | merge as in the scanner's "Merge into Loan" | T-23 |
| `GET /api/loans/{id}/activity` | none | `{items: Activity[]}` | `crm.get_activity` | T-26 |
| `POST /api/loans/import` | multipart `file` (CSV or JSON) | `{imported: number, skipped: number, errors: string[]}` | `crm.bulk_import_loans` | T-24 |
| `GET /api/usage` | none | `UsageSummary` | `tiers.check_scan_quota` | T-27 |
| `GET /api/pricing` | none | `{tiers: Tier[], beta_offer: string, free_beta: boolean}` | `tiers.TIERS`, `tiers.stripe_payment_link`, `product_config.beta_offer` | T-27 |
| `POST /api/tools/{tool}` | `{input: object}` | `{output: object}` | one module per tool, shapes defined in the tool's task | T-30 to T-33 |

## Sandbox behaviour

With `X-PA-Sandbox: 1`: `/api/me` returns `sandbox: true`, `usage: null`; loans come from
`pipeline.sample.json` and writes return `403` with message "Sign in to save changes"; scans
run with local extraction only (`ai_used: false`), are not saved and are not counted.

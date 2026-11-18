// API types. Must match docs/nextjs-rebuild/API_CONTRACT.md and backend/pa_api/models.py.

// ---------- shared ----------
export type ConditionStatus = "Needed" | "Requested" | "Important" | "Ready to Clear" | "Cleared";
export type LoanStatus = "Pending" | "Requested" | "Cleared" | "Overdue" | "Closed";
export type DocType =
  | "Approval Letter" | "Loan Estimate (LE)" | "1003 Application" | "Purchase Contract"
  | "Credit Report" | "Bank Statement" | "Change of Circumstance (COC)" | "Broker Package (BP)"
  | "Pay Stub" | "W-2" | "1099" | "Tax Return" | "Appraisal" | "Title Commitment"
  | "Hazard Insurance" | "Mortgage Statement" | "VA Certificate of Eligibility" | "DD-214"
  | "Government ID" | "Unknown";

export const DOC_TYPES: DocType[] = [
  "Approval Letter", "Loan Estimate (LE)", "1003 Application", "Purchase Contract",
  "Credit Report", "Bank Statement", "Change of Circumstance (COC)", "Broker Package (BP)",
  "Pay Stub", "W-2", "1099", "Tax Return", "Appraisal", "Title Commitment",
  "Hazard Insurance", "Mortgage Statement", "VA Certificate of Eligibility", "DD-214",
  "Government ID", "Unknown",
];
export const LOAN_STATUSES: LoanStatus[] = ["Pending", "Requested", "Cleared", "Overdue", "Closed"];

export interface Condition {
  num: number;
  desc: string;
  party: string;
  status: ConditionStatus;
  section?: string | null;
}

export interface Contact {
  name: string;
  company?: string | null;
  phone?: string | null;
  email?: string | null;
  role?: string | null;
}

export interface ApiErrorBody { error: { code: string; message: string } }

// ---------- account ----------
export interface AiKeyStatus {
  has_key: boolean;
  provider: "gemini";
  model: string;
  last_check: { ok: boolean; message: string; checked_at: string } | null;
}

export interface UsageSummary {
  tier: "free" | "starter" | "pro" | "unlimited";
  tier_name: string;
  limit: number | null;
  used: number;
  remaining: number | null;
  free_beta: boolean;
}

export interface Me {
  user_key: string;
  email: string;
  name: string;
  role: string;
  sandbox: boolean;
  terms_accepted: boolean;
  ai: AiKeyStatus;
  usage: UsageSummary | null;
  features: { more_tools: boolean; owner: boolean; setup_video_url: string | null };
}

export interface TestResult { ok: boolean; message: string }
export interface Ok { ok: boolean }

// ---------- scanning ----------
export interface DetectedFile {
  name: string;
  size_bytes: number;
  detected_type: DocType;
  confidence: "High" | "Medium" | "Low";
}

export interface ScanResult {
  success: boolean;
  doc_type: DocType;
  conditions: Condition[];
  extracted_data: Record<string, unknown>;
  contacts: Record<string, Contact>;
  risks: string;
  image_only: boolean;
  ai_used: boolean;
  ai_note: string;
  error: string;
}

export interface LoanMatch {
  loan_id: number | null;
  loan_num: string;
  borrower: string;
  confidence: number;
  suggestion: "match" | "possible" | "unknown";
}

export interface ScanBatch {
  file: string;
  type: DocType;
  result: ScanResult;
  loan_match: LoanMatch;
}

export type ScanResponse = ScanBatch & { usage: UsageSummary | null };

export interface SavedScan { id: string; saved_at: string; batch: ScanBatch }

// ---------- loans ----------
export interface LoanSummary {
  id: number;
  loan_num: string;
  borrower: string;
  status: LoanStatus;
  closing_date: string;
  lock_expiry: string;
  lock_expired: boolean;
  missing_docs: string;
  assigned_to: string;
  progress_percent: number;
  contacts_line: string;
  updated: string;
}

export interface Loan extends LoanSummary {
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

export interface StatusCounts {
  all: number; pending: number; requested: number; cleared: number; overdue: number; closed: number;
}

export interface LoanCreate {
  loan_num: string;
  borrower: string;
  status: LoanStatus;
  due_date?: string;
  closing_date?: string;
  lock_expiry?: string;
  missing_docs?: string;
  assigned_to?: string;
  property_address?: string;
}

export type LoanUpdate = Partial<Omit<Loan, "id" | "updated" | "progress_percent" | "contacts_line" | "lock_expired">>;

export interface Activity { at: string; action: string; detail: string; user: string }

export type LoanSort = "newest" | "borrower" | "close" | "lock" | "loan_num" | "status";

// ---------- outputs ----------
export interface EmailDraft { subject: string; body: string }
export interface EmailDrafts { borrower_needs_list: EmailDraft; loan_officer_update: EmailDraft }

// ---------- pricing ----------
export interface Tier { key: string; name: string; price: number; scan_limit: number | null; payment_link: string | null }
export interface Pricing { tiers: Tier[]; beta_offer: string; free_beta: boolean }

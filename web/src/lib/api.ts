// Typed client for the Processor Assistant API. One function per endpoint in
// docs/nextjs-rebuild/API_CONTRACT.md. Pages call these; never call fetch directly.
import type {
  Activity, AiKeyStatus, ApiErrorBody, DetectedFile, EmailDrafts, Loan, LoanCreate, LoanSort, LoanStatus, LoanSummary, LoanUpdate, Me, Ok, Pricing, SavedScan, ScanBatch,
  ScanResponse, StatusCounts, TestResult, UsageSummary, Condition, DocType,
} from "./types";
import { supabase } from "./supabase";

type LoanList = { loans: LoanSummary[]; counts: StatusCounts };

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8600";

/** Who is calling. Set by the auth layer (task T-12) after sign-in or sandbox entry. */
let auth: { token: string | null; sandbox: boolean } = { token: null, sandbox: false };
export function setAuth(next: { token: string | null; sandbox: boolean }): void {
  auth = next;
}

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

async function request<T>(method: string, path: string, body?: unknown, raw = false): Promise<T> {
  const headers: Record<string, string> = {};
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) headers.Authorization = `Bearer ${session.access_token}`;
  else if (auth.sandbox || document.cookie.split("; ").includes("pa_sandbox=1")) headers["X-PA-Sandbox"] = "1";
  let payload: BodyInit | undefined;
  if (body instanceof FormData) payload = body;
  else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const res = await fetch(`${BASE}${path}`, { method, headers, body: payload });
  if (!res.ok) {
    let err: ApiErrorBody | null = null;
    try { err = (await res.json()) as ApiErrorBody; } catch { /* non-JSON error */ }
    throw new ApiError(res.status, err?.error.code ?? `http_${res.status}`, err?.error.message ?? "Something went wrong.");
  }
  return (raw ? res.blob() : res.json()) as Promise<T>;
}

// ---------- account ----------
export const getMe = () => request<Me>("GET", "/api/me");
export const acceptTerms = () => request<Ok>("POST", "/api/me/accept-terms");
export const getAiKey = () => request<AiKeyStatus>("GET", "/api/ai-key");
export const saveAiKey = (key: string) => request<AiKeyStatus>("PUT", "/api/ai-key", { key });
export const testAiKey = () => request<TestResult>("POST", "/api/ai-key/test");
export const removeAiKey = () => request<AiKeyStatus>("DELETE", "/api/ai-key");
export const getUsage = () => request<UsageSummary>("GET", "/api/usage");
export const getPricing = () => request<Pricing>("GET", "/api/pricing");

// ---------- scanning ----------
export function detectFiles(files: File[]) {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  return request<{ files: DetectedFile[] }>("POST", "/api/scan/detect", form);
}
export function scanFile(file: File, docType: DocType) {
  const form = new FormData();
  form.append("file", file);
  form.append("doc_type", docType);
  return request<ScanResponse>("POST", "/api/scan", form);
}
export const listScans = () => request<{ items: SavedScan[] }>("GET", "/api/scans");
export const deleteScan = (id: string) => request<Ok>("DELETE", `/api/scans/${encodeURIComponent(id)}`);
export const emailDrafts = (batch: ScanBatch) => request<EmailDrafts>("POST", "/api/outputs/email-drafts", { batch });
export const exportCsv = (batch: ScanBatch) => request<Blob>("POST", "/api/outputs/csv", { batch }, true);
export const exportPdf = (batch: ScanBatch) => request<Blob>("POST", "/api/outputs/pdf", { batch }, true);

// ---------- loans ----------
export function listLoans(opts: { status?: LoanStatus; q?: string; sort?: LoanSort; mine?: boolean } = {}) {
  const params = new URLSearchParams();
  if (opts.status) params.set("status", opts.status);
  if (opts.q) params.set("q", opts.q);
  if (opts.sort) params.set("sort", opts.sort);
  if (opts.mine) params.set("mine", "true");
  const qs = params.toString();
  return request<LoanList>("GET", `/api/loans${qs ? `?${qs}` : ""}`);
}
export const createLoan = (loan: LoanCreate) => request<Loan>("POST", "/api/loans", loan);
export const getLoan = (id: number) => request<Loan>("GET", `/api/loans/${id}`);
export const updateLoan = (id: number, patch: LoanUpdate) => request<Loan>("PATCH", `/api/loans/${id}`, patch);
export const setLoanStatus = (id: number, status: LoanStatus) => request<Loan>("POST", `/api/loans/${id}/status`, { status });
export const setConditions = (id: number, conditions: Condition[]) => request<Loan>("PUT", `/api/loans/${id}/conditions`, { conditions });
export const deleteLoan = (id: number) => request<Ok>("DELETE", `/api/loans/${id}`);
export const removedLoans = () => request<{ loans: LoanSummary[]; retention_days: number }>("GET", "/api/loans/removed");
export const restoreLoan = (id: number) => request<Loan>("POST", `/api/loans/${id}/restore`);
export const loanFromScan = (batch: ScanBatch) => request<Loan>("POST", "/api/loans/from-scan", { batch });
export const mergeScan = (id: number, batch: ScanBatch) =>
  request<{ loan: Loan; added_conditions: number }>("POST", `/api/loans/${id}/merge-scan`, { batch });
export const loanActivity = (id: number) => request<{ items: Activity[] }>("GET", `/api/loans/${id}/activity`);
export function importLoans(file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<{ imported: number; skipped: number; errors: string[] }>("POST", "/api/loans/import", form);
}

// ---------- tools ----------
export const runTool = (tool: string, input: Record<string, unknown>) =>
  request<{ output: Record<string, unknown> }>("POST", `/api/tools/${encodeURIComponent(tool)}`, { input });

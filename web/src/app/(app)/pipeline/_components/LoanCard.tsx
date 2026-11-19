import Link from "next/link";
import type { LoanStatus, LoanSummary } from "@/lib/types";

const STATUSES: LoanStatus[] = [
  "Pending",
  "Requested",
  "Cleared",
  "Overdue",
  "Closed",
];
const STATUS_STYLE: Record<LoanStatus, string> = {
  Pending: "bg-amber-500/10 text-amber-700",
  Requested: "bg-sky-500/10 text-sky-700",
  Cleared: "bg-emerald-500/10 text-emerald-700",
  Overdue: "bg-rose-500/10 text-rose-700",
  Closed: "bg-slate-500/10 text-slate-600",
};

export { STATUSES, STATUS_STYLE };
export default function LoanCard({
  loan,
  onStatus,
  onDelete,
}: {
  loan: LoanSummary;
  onStatus: (id: number, status: LoanStatus) => void;
  onDelete: (id: number) => void;
}) {
  return (
    <article className="animate-fade-up rounded-2xl border border-border bg-card p-5 shadow-card">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link
            href={`/loans/${loan.id}`}
            className="font-semibold text-foreground hover:text-brand"
          >
            {loan.borrower || "Unnamed borrower"}
          </Link>
          <p className="mt-1 text-sm text-muted">Loan {loan.loan_num || "—"}</p>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_STYLE[loan.status]}`}
        >
          <span className="size-1.5 rounded-full bg-current" />
          {loan.status}
        </span>
      </div>
      <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-xs text-muted">Closing</p>
          <p className="mt-1 text-foreground">
            {loan.closing_date || "Not set"}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted">Lock expires</p>
          <p
            className={
              "mt-1 " +
              (loan.lock_expired ? "text-rose-600" : "text-foreground")
            }
          >
            {loan.lock_expiry || "Not set"}
            {loan.lock_expired && " (expired)"}
          </p>
        </div>
      </div>
      <div className="mt-4">
        <div className="flex items-center justify-between text-xs text-muted">
          <span>Conditions cleared</span>
          <span className="tabular-nums text-foreground">
            {loan.progress_percent}%
          </span>
        </div>
        <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-subtle">
          <div
            className="h-full rounded-full bg-emerald-500 transition-all"
            style={{ width: `${loan.progress_percent}%` }}
          />
        </div>
      </div>
      {loan.missing_docs && (
        <p className="mt-3 rounded-lg bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
          Missing: {loan.missing_docs}
        </p>
      )}
      {loan.contacts_line && (
        <p className="mt-3 truncate text-xs text-muted" title={loan.contacts_line}>
          {loan.contacts_line}
        </p>
      )}
      {loan.assigned_to && (
        <p className="mt-2 text-xs text-muted">
          Assigned to{" "}
          <span className="text-foreground">{loan.assigned_to}</span>
        </p>
      )}
      <div className="mt-5 flex items-center gap-2 border-t border-border pt-4">
        <select
          value={loan.status}
          onChange={(event) =>
            onStatus(loan.id, event.target.value as LoanStatus)
          }
          className="rounded-lg border border-border bg-card px-2 py-1.5 text-xs text-foreground"
        >
          <option value={loan.status}>{loan.status}</option>
          {STATUSES.filter((status) => status !== loan.status).map((status) => (
            <option key={status}>{status}</option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => onDelete(loan.id)}
          className="ml-auto text-xs text-muted hover:text-rose-600"
        >
          Remove
        </button>
      </div>
    </article>
  );
}

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
          <p className="text-xs text-muted">Progress</p>
          <p className="mt-1 text-foreground">
            {loan.progress_percent}% cleared
          </p>
        </div>
      </div>
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

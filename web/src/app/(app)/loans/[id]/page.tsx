"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import {
  ArrowLeft,
  CalendarDays,
  CheckCircle2,
  FileText,
  Loader2,
  Save,
} from "lucide-react";
import {
  ApiError,
  draftLoanEmail,
  generateHoiRequest,
  generateTitleRequest,
  getLoan,
  loanActivity,
  setConditions,
  setLoanStatus,
  updateLoan,
} from "@/lib/api";
import type { Activity, Condition, Loan, LoanStatus } from "@/lib/types";

const STATUSES: LoanStatus[] = [
  "Pending",
  "Requested",
  "Cleared",
  "Overdue",
  "Closed",
];
const statusStyle: Record<LoanStatus, string> = {
  Pending: "bg-amber-500/10 text-amber-700",
  Requested: "bg-sky-500/10 text-sky-700",
  Cleared: "bg-emerald-500/10 text-emerald-700",
  Overdue: "bg-rose-500/10 text-rose-700",
  Closed: "bg-slate-500/10 text-slate-600",
};

function StatusPill({ status }: { status: LoanStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${statusStyle[status]}`}
    >
      <span className="size-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}
function Conditions({
  loan,
  onSaved,
}: {
  loan: Loan;
  onSaved: (loan: Loan) => void;
}) {
  const [items, setItems] = useState<Condition[]>(loan.conditions);
  const [busy, setBusy] = useState(false);
  const save = async () => {
    setBusy(true);
    try {
      onSaved(await setConditions(loan.id, items));
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="rounded-2xl border border-border bg-card p-6 shadow-card">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-foreground">Conditions</h2>
        <button
          type="button"
          onClick={() => void save()}
          disabled={busy}
          className="inline-flex items-center gap-2 rounded-xl bg-brand px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
        >
          {busy ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Save className="size-4" />
          )}{" "}
          Save
        </button>
      </div>
      <div className="mt-4 space-y-2">
        {items.length ? (
          items.map((condition, index) => (
            <div
              key={`${condition.num}-${index}`}
              className="flex flex-wrap items-center gap-3 rounded-xl border border-border p-3"
            >
              <span className="flex-1 text-sm text-foreground">
                {condition.desc}
              </span>
              <span className="text-xs text-muted">{condition.party}</span>
              <select
                value={condition.status}
                onChange={(event) =>
                  setItems(
                    items.map((item, itemIndex) =>
                      itemIndex === index
                        ? {
                            ...item,
                            status: event.target.value as Condition["status"],
                          }
                        : item,
                    ),
                  )
                }
                className="rounded-lg border border-border bg-card px-2 py-1 text-xs text-foreground"
              >
                <option>Needed</option>
                <option>Requested</option>
                <option>Important</option>
                <option>Ready to Clear</option>
                <option>Cleared</option>
              </select>
            </div>
          ))
        ) : (
          <p className="py-6 text-center text-sm text-muted">
            No conditions have been added yet.
          </p>
        )}
      </div>
    </section>
  );
}

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [loan, setLoan] = useState<Loan | null>(null);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    getLoan(Number(id))
      .then((value) => {
        setLoan(value);
        setNotes(value.notes);
      })
      .catch((e) =>
        setError(
          e instanceof ApiError ? e.message : "Could not load this loan.",
        ),
      );
    loanActivity(Number(id))
      .then((value) => setActivity(value.items))
      .catch(() => undefined);
  }, [id]);
  const status = async (value: LoanStatus) => {
    if (!loan) return;
    setBusy(true);
    try {
      setLoan(await setLoanStatus(loan.id, value));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not change status.");
    } finally {
      setBusy(false);
    }
  };
  const saveNotes = async () => {
    if (!loan) return;
    setBusy(true);
    try {
      setLoan(await updateLoan(loan.id, { notes }));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not save notes.");
    } finally {
      setBusy(false);
    }
  };
  if (error)
    return (
      <div className="mx-auto max-w-5xl px-4 py-8 md:px-8">
        <p className="rounded-xl border border-rose-500/25 bg-rose-500/[0.07] p-4 text-sm text-rose-600">
          {error}
        </p>
      </div>
    );
  if (!loan)
    return (
      <div className="mx-auto max-w-5xl px-4 py-8 md:px-8">
        <Loader2 className="size-5 animate-spin text-muted" />
      </div>
    );
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 md:px-8">
      <Link
        href="/pipeline"
        className="inline-flex items-center gap-2 text-sm text-muted hover:text-brand"
      >
        <ArrowLeft className="size-4" /> Back to pipeline
      </Link>
      <header className="mt-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">
            Loan detail
          </p>
          <h1 className="mt-2 text-[28px] font-semibold tracking-tight text-foreground">
            {loan.borrower}
          </h1>
          <p className="mt-1 text-sm text-muted">Loan {loan.loan_num}</p>
        </div>
        <StatusPill status={loan.status} />
      </header>
      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-border bg-card p-5 shadow-card">
          <CalendarDays className="size-5 text-brand" />
          <p className="mt-4 text-xs text-muted">Closing date</p>
          <p className="mt-1 font-medium text-foreground">
            {loan.closing_date || "Not set"}
          </p>
        </div>
        <div className="rounded-2xl border border-border bg-card p-5 shadow-card">
          <CheckCircle2 className="size-5 text-emerald-600" />
          <p className="mt-4 text-xs text-muted">Progress</p>
          <p className="mt-1 font-medium text-foreground">
            {loan.progress_percent}% cleared
          </p>
        </div>
        <div className="rounded-2xl border border-border bg-card p-5 shadow-card">
          <FileText className="size-5 text-brand" />
          <p className="mt-4 text-xs text-muted">Documents</p>
          <p className="mt-1 font-medium text-foreground">
            {loan.documents.length} attached
          </p>
        </div>
      </div>
      <section className="mt-6 rounded-2xl border border-border bg-card p-6 shadow-card">
        <h2 className="font-semibold text-foreground">Loan status</h2>
        <div className="mt-4 flex flex-wrap gap-2">
          {STATUSES.map((value) => (
            <button
              type="button"
              key={value}
              disabled={busy}
              onClick={() => void status(value)}
              className={`rounded-xl border px-3 py-2 text-sm ${loan.status === value ? "border-brand bg-brand-soft text-brand" : "border-border bg-card text-foreground"}`}
            >
              {value}
            </button>
          ))}
        </div>
      </section>
      <section className="mt-6 rounded-2xl border border-border bg-card p-6 shadow-card">
        <h2 className="font-semibold text-foreground">Activity</h2>
        {activity.length ? (
          <div className="mt-4 space-y-3">
            {activity.map((item, index) => (
              <div
                key={`${item.at}-${index}`}
                className="border-l-2 border-brand/30 pl-3"
              >
                <p className="text-sm text-foreground">{item.detail}</p>
                <p className="mt-1 text-xs text-muted">
                  {item.action} · {item.at}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm text-muted">No activity recorded yet.</p>
        )}
      </section>
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Conditions loan={loan} onSaved={setLoan} />
        <section className="rounded-2xl border border-border bg-card p-6 shadow-card">
          <h2 className="font-semibold text-foreground">Notes</h2>
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            rows={8}
            placeholder="Add notes about this loan"
            className="mt-4 w-full rounded-xl border border-border bg-surface p-3 text-sm text-foreground"
          />
          <button
            type="button"
            disabled={busy}
            onClick={() => void saveNotes()}
            className="mt-3 inline-flex items-center gap-2 rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
          >
            {busy ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Save className="size-4" />
            )}{" "}
            Save notes
          </button>
        </section>
      </div>
      <section id="scan-into-loan" />
      {/* Claude will add the scan-into-loan control with T-23 merge-scan. */}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-border bg-card p-6 shadow-card">
          <h2 className="font-semibold text-foreground">Contacts</h2>
          {Object.keys(loan.contacts).length ? (
            <div className="mt-4 space-y-3">
              {Object.entries(loan.contacts).map(([role, contact]) => (
                <div key={role} className="rounded-xl border border-border p-3">
                  <p className="text-xs font-semibold uppercase text-muted">
                    {role.replaceAll("_", " ")}
                  </p>
                  <p className="mt-1 text-sm text-foreground">
                    {contact.name || contact.company || "Unnamed contact"}
                  </p>
                  {contact.email && (
                    <p className="text-xs text-muted">{contact.email}</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm text-muted">
              No contacts have been added.
            </p>
          )}
        </section>
        <section className="rounded-2xl border border-border bg-card p-6 shadow-card">
          <h2 className="font-semibold text-foreground">Documents</h2>
          {loan.documents.length ? (
            <div className="mt-4 space-y-2">
              {loan.documents.map((document) => (
                <div
                  key={document.filename}
                  className="flex items-center justify-between rounded-xl border border-border p-3 text-sm"
                >
                  <span className="text-foreground">{document.filename}</span>
                  <span className="text-xs text-muted">
                    {document.doc_type}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm text-muted">
              No documents have been attached.
            </p>
          )}
        </section>
      </div>
      <section className="mt-6 rounded-2xl border border-border bg-card p-6 shadow-card">
        <h2 className="font-semibold text-foreground">Request drafts</h2>
        <p className="mt-1 text-sm text-muted">
          Generate text you can review and send yourself.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void draftLoanEmail(loan.id)}
            className="rounded-xl border border-border bg-card px-4 py-2 text-sm text-foreground"
          >
            Draft email
          </button>
          <button
            type="button"
            onClick={() => void generateHoiRequest(loan.id)}
            className="rounded-xl border border-border bg-card px-4 py-2 text-sm text-foreground"
          >
            HOI request
          </button>
          <button
            type="button"
            onClick={() => void generateTitleRequest(loan.id)}
            className="rounded-xl border border-border bg-card px-4 py-2 text-sm text-foreground"
          >
            Title request
          </button>
        </div>
      </section>
    </div>
  );
}

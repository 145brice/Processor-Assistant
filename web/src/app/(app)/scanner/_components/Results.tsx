"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronRight, Sparkles, XCircle } from "lucide-react";
import type { ScanBatch } from "@/lib/types";
import LoanActions from "./LoanActions";
import { ContactsGrid, EmailDraftsPanel, FieldsTable, OutputActions, borrowerOf } from "./ResultDetails";

const PARTY_STYLE: Record<string, string> = {
  Borrower: "bg-sky-500/10 text-sky-700 dark:text-sky-300",
  Title: "bg-violet-500/10 text-violet-700 dark:text-violet-300",
  Underwriter: "bg-rose-500/10 text-rose-700 dark:text-rose-300",
  Insurance: "bg-amber-500/10 text-amber-700 dark:text-amber-300",
  Appraiser: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
};

function Conditions({ batch }: { batch: ScanBatch }) {
  const rows = batch.result.conditions;
  if (!rows.length) return null;
  return (
    <section>
      <h3 className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">
        Conditions <span className="rounded bg-subtle px-1.5 py-px text-[10px] tracking-normal">{rows.length}</span>
      </h3>
      <ol className="divide-y divide-border overflow-hidden rounded-xl border border-border">
        {rows.map((c) => (
          <li key={c.num} className="flex items-start gap-3 px-4 py-3 text-sm">
            <span className="w-6 shrink-0 pt-0.5 text-right text-xs font-medium tabular-nums text-muted">{c.num}</span>
            <span className="min-w-0 flex-1 text-foreground">
              {c.desc}
              {c.section && <span className="ml-2 rounded bg-subtle px-1.5 py-px text-[10px] font-medium text-muted">{c.section}</span>}
            </span>
            <span className={"shrink-0 rounded-full px-2 py-0.5 text-xs font-medium " + (PARTY_STYLE[c.party] ?? "bg-subtle text-muted")}>
              {c.party}
            </span>
            <span className="hidden w-24 shrink-0 text-right text-xs text-muted sm:block">{c.status}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

function ResultCard({ batch, defaultOpen }: { batch: ScanBatch; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const r = batch.result;
  const borrower = borrowerOf(batch);
  const summary = [batch.type, borrower, batch.loan_match.loan_num && `Loan ${batch.loan_match.loan_num}`]
    .filter(Boolean)
    .join(" · ");

  return (
    <article className="animate-fade-up overflow-hidden rounded-2xl border border-border bg-card shadow-card transition hover:shadow-md">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="flex w-full items-center gap-4 px-5 py-4 text-left"
      >
        <div className={"grid size-10 shrink-0 place-items-center rounded-xl " +
          (r.success ? "bg-emerald-500/10 text-emerald-600" : "bg-rose-500/10 text-rose-600")}>
          {r.success ? <CheckCircle2 className="size-5" /> : <XCircle className="size-5" />}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium text-foreground" title={batch.file}>{batch.file}</p>
          <p className="mt-0.5 truncate text-xs text-muted">
            {summary}
            {r.success && ` · ${r.conditions.length} condition${r.conditions.length === 1 ? "" : "s"}`}
          </p>
        </div>
        {r.ai_used && (
          <span className="hidden items-center gap-1 rounded-full bg-brand-soft px-2.5 py-1 text-xs font-medium text-brand sm:inline-flex">
            <Sparkles className="size-3" /> AI enhanced
          </span>
        )}
        {batch.loan_match.suggestion !== "unknown" && (
          <span className="hidden rounded-full bg-subtle px-2.5 py-1 text-xs font-medium text-foreground md:inline">
            {batch.loan_match.suggestion === "match" ? "Matches" : "Possible match:"} {batch.loan_match.borrower || batch.loan_match.loan_num}
          </span>
        )}
        <ChevronRight className={"size-4 shrink-0 text-muted transition-transform " + (open ? "rotate-90" : "")} />
      </button>

      {open && (
        <div className="space-y-6 border-t border-border px-5 py-5">
          {!r.success && (
            <p className="rounded-xl bg-rose-500/[0.07] px-4 py-3 text-sm text-rose-700 dark:text-rose-300">{r.error}</p>
          )}
          {r.image_only && (
            <p className="flex items-start gap-2 rounded-xl bg-amber-500/[0.07] px-4 py-3 text-sm text-foreground">
              <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" />
              This is a scanned image with no readable text. It was logged without extraction.
            </p>
          )}

          {r.success && (
            <>
              <LoanActions batch={batch} />
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs text-muted">{r.ai_note}</p>
                <OutputActions batch={batch} />
              </div>
              <ContactsGrid contacts={r.contacts} />
              <FieldsTable data={r.extracted_data} />
              <Conditions batch={batch} />
              {r.risks && (
                <section>
                  <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">Notes</h3>
                  <p className="whitespace-pre-line rounded-xl border border-border bg-surface px-4 py-3 text-[13px] text-foreground">
                    {r.risks}
                  </p>
                </section>
              )}
              <EmailDraftsPanel batch={batch} />
            </>
          )}
        </div>
      )}
    </article>
  );
}

export default function Results({ batches, onClear }: { batches: ScanBatch[]; onClear: () => void }) {
  if (!batches.length) return null;
  return (
    <section className="mt-8">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-foreground">
          Results <span className="ml-1 rounded-full bg-subtle px-2 py-0.5 text-xs font-medium text-muted">{batches.length}</span>
        </h2>
        <button
          type="button"
          onClick={onClear}
          className="rounded-md px-2 py-1 text-xs font-medium text-muted transition hover:bg-subtle hover:text-foreground"
        >
          Clear all
        </button>
      </div>
      <div className="space-y-3">
        {batches.map((b, i) => <ResultCard key={`${b.file}-${i}`} batch={b} defaultOpen={i === 0} />)}
      </div>
    </section>
  );
}

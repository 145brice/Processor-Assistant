"use client";

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Sparkles,
  XCircle,
} from "lucide-react";
import type { Condition, ConditionStatus, ScanBatch } from "@/lib/types";
import LoanActions from "./LoanActions";
import {
  ContactsGrid,
  EmailDraftsPanel,
  FieldsTable,
  OutputActions,
  borrowerOf,
} from "./ResultDetails";

const PARTY_OPTIONS = [
  "Borrower",
  "Co-Borrower",
  "Title",
  "Realtor",
  "Seller",
  "Processor",
  "Underwriter",
  "Jr Underwriter",
  "Loan Officer",
  "Closer",
  "Insurance",
  "Appraiser",
  "Employer",
  "Manager",
];

const STATUS_OPTIONS: ConditionStatus[] = [
  "Needed",
  "Requested",
  "Important",
  "Ready to Clear",
  "Cleared",
];

function isEmailInstruction(condition: Condition): boolean {
  const text = condition.desc.trim().replace(/\s+/g, " ");
  return /^select the (?:named )?part(?:y|ies|ys) below to draft emails?$/i.test(
    text,
  );
}

const selectClass =
  "min-h-9 rounded-lg border border-transparent bg-subtle/80 px-2.5 py-1.5 text-xs font-medium " +
  "text-foreground outline-none transition hover:bg-subtle focus:border-brand/40 focus:bg-card " +
  "focus:ring-2 focus:ring-brand/15";

function Conditions({
  batch,
  onChange,
}: {
  batch: ScanBatch;
  onChange: (index: number, change: Partial<Condition>) => void;
}) {
  const rows = batch.result.conditions;
  if (!rows.length) return null;
  return (
    <section>
      <div className="mb-3 flex items-end justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-brand">
            Conditions
          </p>
          <h3 className="mt-1 text-lg font-semibold tracking-tight text-foreground">
            Review responsibilities
          </h3>
        </div>
        <span className="rounded-full bg-brand-soft px-2.5 py-1 text-[11px] font-semibold text-brand">
          {rows.length}
        </span>
      </div>
      <div className="hidden grid-cols-[2rem_minmax(0,1fr)_10rem_9rem] gap-3 border-b border-border/70 px-2 pb-2 text-[10px] font-semibold uppercase tracking-[0.1em] text-muted sm:grid">
        <span>#</span>
        <span>Condition</span>
        <span>Responsible</span>
        <span>Status</span>
      </div>
      <ol className="divide-y divide-border/70">
        {rows.map((c, index) => (
          <li
            key={`${c.num}-${index}`}
            className="grid gap-3 px-2 py-3.5 text-sm transition hover:bg-subtle/40 sm:grid-cols-[2rem_minmax(0,1fr)_10rem_9rem]"
          >
            <span className="w-6 shrink-0 pt-0.5 text-right text-xs font-medium tabular-nums text-muted">
              {c.num}
            </span>
            <span className="min-w-0 flex-1 text-foreground">
              {c.desc}
              {c.section && (
                <span className="ml-2 rounded bg-subtle px-1.5 py-px text-[10px] font-medium text-muted">
                  {c.section}
                </span>
              )}
            </span>
            <label className="grid gap-1">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-muted sm:sr-only">
                Responsible party
              </span>
              <select
                aria-label={`Responsible party for condition ${c.num}`}
                value={c.party}
                onChange={(event) =>
                  onChange(index, { party: event.target.value })
                }
                className={selectClass}
              >
                {!PARTY_OPTIONS.includes(c.party) && (
                  <option value={c.party}>{c.party}</option>
                )}
                {PARTY_OPTIONS.map((party) => (
                  <option key={party} value={party}>
                    {party}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-1">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-muted sm:sr-only">
                Status
              </span>
              <select
                aria-label={`Status for condition ${c.num}`}
                value={c.status}
                onChange={(event) =>
                  onChange(index, {
                    status: event.target.value as ConditionStatus,
                  })
                }
                className={selectClass}
              >
                {STATUS_OPTIONS.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </label>
          </li>
        ))}
      </ol>
    </section>
  );
}

function ResultCard({
  batch,
  defaultOpen,
}: {
  batch: ScanBatch;
  defaultOpen: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const [editedBatch, setEditedBatch] = useState<ScanBatch>(() => ({
    ...batch,
    result: {
      ...batch.result,
      conditions: batch.result.conditions.filter(
        (condition) => !isEmailInstruction(condition),
      ),
    },
  }));
  const r = editedBatch.result;
  const borrower = borrowerOf(editedBatch);
  const summary = [
    editedBatch.type,
    borrower,
    editedBatch.loan_match.loan_num &&
      `Loan ${editedBatch.loan_match.loan_num}`,
  ]
    .filter(Boolean)
    .join(" · ");

  const updateCondition = (index: number, change: Partial<Condition>) => {
    setEditedBatch((current) => ({
      ...current,
      result: {
        ...current.result,
        conditions: current.result.conditions.map(
          (condition, conditionIndex) =>
            conditionIndex === index ? { ...condition, ...change } : condition,
        ),
      },
    }));
  };

  return (
    <article className="animate-fade-up overflow-hidden rounded-[24px] bg-card shadow-[0_20px_55px_-42px_rgba(15,23,42,0.55)] ring-1 ring-black/[0.04] dark:ring-white/[0.07]">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="flex w-full items-center gap-4 bg-gradient-to-r from-brand/[0.07] via-transparent to-transparent px-6 py-5 text-left"
      >
        <div
          className={
            "grid size-11 shrink-0 place-items-center rounded-full ring-1 ring-current/10 " +
            (r.success
              ? "bg-emerald-500/10 text-emerald-600"
              : "bg-rose-500/10 text-rose-600")
          }
        >
          {r.success ? (
            <CheckCircle2 className="size-5" />
          ) : (
            <XCircle className="size-5" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p
            className="truncate text-[15px] font-semibold tracking-tight text-foreground"
            title={editedBatch.file}
          >
            {editedBatch.file}
          </p>
          <p className="mt-0.5 truncate text-xs text-muted">
            {summary}
            {r.success &&
              ` · ${r.conditions.length} condition${r.conditions.length === 1 ? "" : "s"}`}
          </p>
        </div>
        {r.ai_used && (
          <span className="hidden items-center gap-1 rounded-full bg-brand-soft px-2.5 py-1 text-xs font-medium text-brand sm:inline-flex">
            <Sparkles className="size-3" /> AI enhanced
          </span>
        )}
        {editedBatch.loan_match.suggestion !== "unknown" && (
          <span className="hidden rounded-full bg-subtle px-2.5 py-1 text-xs font-medium text-foreground md:inline">
            {editedBatch.loan_match.suggestion === "match"
              ? "Matches"
              : "Possible match:"}{" "}
            {editedBatch.loan_match.borrower || editedBatch.loan_match.loan_num}
          </span>
        )}
        <ChevronRight
          className={
            "size-4 shrink-0 text-muted transition-transform " +
            (open ? "rotate-90" : "")
          }
        />
      </button>

      {open && (
        <div className="space-y-7 border-t border-border/60 px-6 py-6">
          {!r.success && (
            <p className="rounded-xl bg-rose-500/[0.07] px-4 py-3 text-sm text-rose-700 dark:text-rose-300">
              {r.error}
            </p>
          )}
          {r.image_only && (
            <p className="flex items-start gap-2 rounded-xl bg-amber-500/[0.07] px-4 py-3 text-sm text-foreground">
              <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" />
              This is a scanned image with no readable text. It was logged
              without extraction.
            </p>
          )}

          {r.success && (
            <>
              <LoanActions batch={editedBatch} />
              <div className="grid gap-5 border-y border-border/70 py-5 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-start">
                <EmailDraftsPanel batch={editedBatch} />
                <div className="lg:text-right">
                  <p className="mb-2 text-xs text-muted">{r.ai_note}</p>
                  <OutputActions batch={editedBatch} />
                </div>
              </div>
              <ContactsGrid contacts={r.contacts} />
              <FieldsTable data={r.extracted_data} />
              <Conditions batch={editedBatch} onChange={updateCondition} />
              {r.risks && (
                <section>
                  <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">
                    Notes
                  </h3>
                  <p className="whitespace-pre-line border-l-2 border-brand/30 pl-4 text-[13px] leading-relaxed text-foreground">
                    {r.risks}
                  </p>
                </section>
              )}
            </>
          )}
        </div>
      )}
    </article>
  );
}

export default function Results({
  batches,
  onClear,
}: {
  batches: ScanBatch[];
  onClear: () => void;
}) {
  if (!batches.length) return null;
  return (
    <section className="mt-8">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-foreground">
          Results{" "}
          <span className="ml-1 rounded-full bg-subtle px-2 py-0.5 text-xs font-medium text-muted">
            {batches.length}
          </span>
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
        {batches.map((b, i) => (
          <ResultCard key={`${b.file}-${i}`} batch={b} defaultOpen={i === 0} />
        ))}
      </div>
    </section>
  );
}

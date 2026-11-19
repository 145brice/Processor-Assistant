"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronRight, Sparkles, Users, XCircle } from "lucide-react";
import type { ScanBatch } from "@/lib/types";

const PARTY_STYLE: Record<string, string> = {
  Borrower: "bg-sky-500/10 text-sky-700 dark:text-sky-300",
  Title: "bg-violet-500/10 text-violet-700 dark:text-violet-300",
  Underwriter: "bg-rose-500/10 text-rose-700 dark:text-rose-300",
  Insurance: "bg-amber-500/10 text-amber-700 dark:text-amber-300",
  Appraiser: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
};

function ResultCard({ batch, defaultOpen }: { batch: ScanBatch; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const r = batch.result;
  const contactCount = Object.keys(r.contacts).length;
  const fieldCount = Object.keys(r.extracted_data).length;

  return (
    <article className="animate-fade-up overflow-hidden rounded-2xl border border-border bg-card shadow-card transition hover:shadow-md">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="flex w-full items-center gap-4 px-5 py-4 text-left">
        <div className={"grid size-10 shrink-0 place-items-center rounded-xl " + (r.success ? "bg-emerald-500/10 text-emerald-600" : "bg-rose-500/10 text-rose-600")}>
          {r.success ? <CheckCircle2 className="size-5" /> : <XCircle className="size-5" />}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium text-foreground" title={batch.file}>{batch.file}</p>
          <p className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
            <span>{batch.type}</span>
            {r.success && <span>{r.conditions.length} condition{r.conditions.length === 1 ? "" : "s"}</span>}
            {r.success && contactCount > 0 && <span className="inline-flex items-center gap-1"><Users className="size-3" />{contactCount} contact{contactCount === 1 ? "" : "s"}</span>}
            {r.success && fieldCount > 0 && <span>{fieldCount} field{fieldCount === 1 ? "" : "s"}</span>}
            {r.ai_used && <span className="inline-flex items-center gap-1 text-brand"><Sparkles className="size-3" />AI enhanced</span>}
          </p>
        </div>
        {batch.loan_match.suggestion !== "unknown" && (
          <span className="hidden rounded-full bg-brand-soft px-2.5 py-1 text-xs font-medium text-brand sm:inline">
            {batch.loan_match.suggestion === "match" ? "Matches" : "Maybe"} {batch.loan_match.borrower || batch.loan_match.loan_num}
          </span>
        )}
        <ChevronRight className={"size-4 shrink-0 text-muted transition-transform " + (open ? "rotate-90" : "")} />
      </button>

      {open && (
        <div className="space-y-4 border-t border-border px-5 py-4">
          {!r.success && <p className="rounded-xl bg-rose-500/[0.07] px-4 py-3 text-sm text-rose-700 dark:text-rose-300">{r.error}</p>}
          {r.image_only && (
            <p className="flex items-start gap-2 rounded-xl bg-amber-500/[0.07] px-4 py-3 text-sm text-foreground">
              <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" />
              This is a scanned image with no readable text. It was logged without extraction.
            </p>
          )}
          {r.ai_note && <p className="text-xs text-muted">{r.ai_note}</p>}

          {r.conditions.length > 0 && (
            <ol className="divide-y divide-border rounded-xl border border-border">
              {r.conditions.map((c) => (
                <li key={c.num} className="flex items-start gap-3 px-4 py-3 text-sm">
                  <span className="w-6 shrink-0 pt-0.5 text-right text-xs font-medium tabular-nums text-muted">{c.num}</span>
                  <span className="min-w-0 flex-1 text-foreground">{c.desc}</span>
                  <span className={"shrink-0 rounded-full px-2 py-0.5 text-xs font-medium " + (PARTY_STYLE[c.party] ?? "bg-subtle text-muted")}>{c.party}</span>
                  <span className="hidden w-24 shrink-0 text-right text-xs text-muted sm:block">{c.status}</span>
                </li>
              ))}
            </ol>
          )}

          {r.success && r.conditions.length === 0 && !r.image_only && (
            <p className="text-sm text-muted">No conditions in this document. Fields, contacts, exports and loan actions come with the full result view.</p>
          )}
        </div>
      )}
    </article>
  );
}

export default function Results({ batches }: { batches: ScanBatch[] }) {
  if (!batches.length) return null;
  return (
    <section className="mt-8">
      <h2 className="mb-3 text-sm font-semibold text-foreground">
        Results <span className="ml-1 rounded-full bg-subtle px-2 py-0.5 text-xs font-medium text-muted">{batches.length}</span>
      </h2>
      <div className="space-y-3">
        {batches.map((b, i) => <ResultCard key={`${b.file}-${i}`} batch={b} defaultOpen={i === 0} />)}
      </div>
    </section>
  );
}

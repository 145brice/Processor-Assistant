"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowUpRight, CheckCircle2, GitMerge, Link2, Loader2, Plus, SearchCheck } from "lucide-react";
import { ApiError, loanFromScan, mergeScan } from "@/lib/api";
import type { ScanBatch } from "@/lib/types";
import { borrowerOf } from "./ResultDetails";

type Done = { kind: "merged" | "created"; loanId: number; text: string };

const button =
  "inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-[13px] font-medium " +
  "text-foreground shadow-card transition hover:border-brand/40 hover:bg-subtle disabled:opacity-50";
const primary =
  "inline-flex items-center gap-1.5 rounded-lg bg-brand px-3 py-1.5 text-[13px] font-medium text-white " +
  "shadow-sm transition hover:bg-brand-strong disabled:opacity-50";

/** Same choices as the Streamlit scanner's loan-match row. */
export default function LoanActions({ batch }: { batch: ScanBatch }) {
  const match = batch.loan_match;
  const [busy, setBusy] = useState<"merge" | "create" | null>(null);
  const [done, setDone] = useState<Done | null>(null);
  const [error, setError] = useState("");

  const run = async (kind: "merge" | "create") => {
    setBusy(kind);
    setError("");
    try {
      if (kind === "merge" && match.loan_id !== null) {
        const result = await mergeScan(match.loan_id, batch);
        const text = batch.type === "Purchase Contract"
          ? `Purchase contract merged into loan ${result.loan.loan_num}: contacts and dates updated.`
          : `${result.added_conditions} condition${result.added_conditions === 1 ? "" : "s"} merged into loan ${result.loan.loan_num}.`;
        setDone({ kind: "merged", loanId: result.loan.id, text });
      } else {
        const loan = await loanFromScan(batch);
        setDone({ kind: "created", loanId: loan.id, text: `Loan created for ${loan.borrower}.` });
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "That didn't go through. Try again.");
    } finally {
      setBusy(null);
    }
  };

  if (!batch.result.success) return null;

  if (done) {
    return (
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-emerald-500/25 bg-emerald-500/[0.07] px-4 py-3 text-[13px]">
        <CheckCircle2 className="size-4 shrink-0 text-emerald-600" />
        <span className="flex-1 text-foreground">{done.text}</span>
        <Link href={`/loans/${done.loanId}`} className={button}>
          Open loan <ArrowUpRight className="size-3.5" />
        </Link>
      </div>
    );
  }

  const spinner = (kind: "merge" | "create") => busy === kind && <Loader2 className="size-3.5 animate-spin" />;
  const borrower = borrowerOf(batch);

  return (
    <div>
      {match.suggestion === "match" && match.loan_id !== null && (
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-brand/25 bg-brand-soft px-4 py-3 text-[13px]">
          <Link2 className="size-4 shrink-0 text-brand" />
          <span className="flex-1 text-foreground">
            <b>Matched:</b> Loan {match.loan_num} · {match.borrower}
            <span className="text-muted"> ({match.confidence}% confidence)</span>
          </span>
          <Link href={`/loans/${match.loan_id}`} className={button}>Open loan</Link>
          <button type="button" className={primary} disabled={busy !== null} onClick={() => void run("merge")}>
            {spinner("merge") || <GitMerge className="size-3.5" />} Merge into loan
          </button>
        </div>
      )}

      {match.suggestion === "possible" && match.loan_id !== null && (
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/[0.07] px-4 py-3 text-[13px]">
          <SearchCheck className="size-4 shrink-0 text-amber-600" />
          <span className="flex-1 text-foreground">
            <b>Possible match:</b> {match.borrower} (Loan {match.loan_num})
            <span className="text-muted"> · {match.confidence}% confidence, verify before merging</span>
          </span>
          <Link href={`/loans/${match.loan_id}`} target="_blank" className={button}>
            Open &amp; verify <ArrowUpRight className="size-3.5" />
          </Link>
          <button type="button" className={button} disabled={busy !== null} onClick={() => void run("merge")}>
            {spinner("merge") || <GitMerge className="size-3.5" />} Merge into this loan
          </button>
          <button type="button" className={button} disabled={busy !== null} onClick={() => void run("create")}>
            {spinner("create") || <Plus className="size-3.5" />} Start new loan instead
          </button>
        </div>
      )}

      {(match.suggestion === "unknown" || match.loan_id === null) && (
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3 text-[13px]">
          <span className="flex-1 text-muted">
            <b className="text-foreground">No pipeline match found.</b>
            {borrower && <> Borrower extracted: <b className="text-foreground">{borrower}</b></>}
          </span>
          <button type="button" className={primary} disabled={busy !== null} onClick={() => void run("create")}>
            {spinner("create") || <Plus className="size-3.5" />} Start new loan from this doc
          </button>
        </div>
      )}

      {error && <p className="mt-2 text-xs text-rose-600">{error}</p>}
    </div>
  );
}

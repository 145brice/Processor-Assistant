"use client";

import { useRef, useState } from "react";
import { CheckCircle2, FileText, Loader2, ScanLine, UploadCloud, X } from "lucide-react";
import { ApiError, detectFiles, mergeScan, scanFile } from "@/lib/api";
import { DOC_TYPES, type DocType, type Loan } from "@/lib/types";

type Stage = "pick" | "detecting" | "ready" | "scanning";

/**
 * Upload one PDF, check its detected type, then scan it and merge the result into this loan
 * (POST /api/scan, then POST /api/loans/{id}/merge-scan). The PDF is never stored.
 */
export default function ScanIntoLoan({ loanId, onMerged }: { loanId: number; onMerged: (loan: Loan) => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [type, setType] = useState<DocType>("Unknown");
  const [stage, setStage] = useState<Stage>("pick");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const reset = () => {
    setFile(null);
    setType("Unknown");
    setStage("pick");
  };

  const choose = async (picked: File | undefined) => {
    if (!picked) return;
    setError("");
    setMessage("");
    if (!picked.name.toLowerCase().endsWith(".pdf") && picked.type !== "application/pdf") {
      setError(`${picked.name} is not a PDF.`);
      return;
    }
    if (picked.size > 40 * 1024 * 1024) {
      setError(`${picked.name} is over the 40 MB limit.`);
      return;
    }
    setFile(picked);
    setStage("detecting");
    try {
      const { files } = await detectFiles([picked]);
      setType(files[0]?.detected_type ?? "Unknown");
    } catch {
      setType("Unknown");
    }
    setStage("ready");
  };

  const scanAndMerge = async () => {
    if (!file || type === "Unknown") return;
    setStage("scanning");
    setError("");
    try {
      const { usage: _usage, ...batch } = await scanFile(file, type);
      void _usage;
      if (!batch.result.success) {
        setError(batch.result.error || "This document could not be read.");
        setStage("ready");
        return;
      }
      const merged = await mergeScan(loanId, batch);
      onMerged(merged.loan);
      setMessage(
        type === "Purchase Contract"
          ? `${file.name} merged: contacts and dates updated.`
          : `${file.name} merged: ${merged.added_conditions} new condition${merged.added_conditions === 1 ? "" : "s"} added.`,
      );
      reset();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "The scan didn't finish. Try again.");
      setStage("ready");
    }
  };

  return (
    <section className="mt-6 rounded-2xl border border-border bg-card p-5 shadow-card">
      <div className="flex items-center gap-3">
        <span className="grid size-9 place-items-center rounded-xl bg-brand-soft text-brand">
          <ScanLine className="size-4" />
        </span>
        <div>
          <h2 className="font-semibold text-foreground">Scan a document into this loan</h2>
          <p className="text-xs text-muted">New conditions, contacts and dates are added. Existing ones are kept.</p>
        </div>
      </div>

      {stage === "pick" && (
        <button
          type="button"
          onClick={() => input.current?.click()}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-surface px-4 py-6 text-sm text-muted transition hover:border-brand/50 hover:text-foreground"
        >
          <UploadCloud className="size-5 text-brand" /> Choose a PDF (up to 40 MB)
        </button>
      )}

      {file && stage !== "pick" && (
        <div className="mt-4 flex flex-wrap items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3">
          <FileText className="size-4 shrink-0 text-muted" />
          <span className="min-w-0 flex-1 truncate text-sm font-medium text-foreground" title={file.name}>{file.name}</span>
          {stage === "detecting" ? (
            <span className="skeleton animate-shimmer h-9 w-52 rounded-lg" aria-label="Detecting type" />
          ) : (
            <select
              aria-label="Document type"
              value={type}
              disabled={stage === "scanning"}
              onChange={(e) => setType(e.target.value as DocType)}
              className="h-9 w-52 rounded-lg border border-border bg-card px-2.5 text-sm text-foreground focus:border-brand focus:outline-none"
            >
              {DOC_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          )}
          <button
            type="button"
            onClick={() => void scanAndMerge()}
            disabled={stage !== "ready" || type === "Unknown"}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-3.5 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-brand-strong disabled:opacity-50"
          >
            {stage === "scanning" ? <Loader2 className="size-4 animate-spin" /> : <ScanLine className="size-4" />}
            {stage === "scanning" ? "Scanning…" : "Scan and merge"}
          </button>
          <button type="button" onClick={reset} disabled={stage === "scanning"} aria-label="Cancel"
            className="grid size-8 place-items-center rounded-lg text-muted hover:bg-subtle hover:text-foreground disabled:opacity-50">
            <X className="size-4" />
          </button>
        </div>
      )}
      {type === "Unknown" && stage === "ready" && <p className="mt-2 text-xs text-muted">Choose the document type to scan it.</p>}

      {message && (
        <p className="mt-3 flex items-center gap-2 text-sm text-emerald-700 dark:text-emerald-400">
          <CheckCircle2 className="size-4" /> {message}
        </p>
      )}
      {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}

      <input ref={input} type="file" accept="application/pdf,.pdf" hidden
        onChange={(e) => { void choose(e.target.files?.[0]); e.target.value = ""; }} />
    </section>
  );
}

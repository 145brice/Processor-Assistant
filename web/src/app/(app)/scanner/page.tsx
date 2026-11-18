"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle, ChevronRight, FileSpreadsheet, KeyRound, Loader2, ScanLine, ShieldCheck } from "lucide-react";
import { ApiError, detectFiles, getMe, scanFile } from "@/lib/api";
import type { ScanBatch, UsageSummary } from "@/lib/types";
import Dropzone from "./_components/Dropzone";
import FileList, { type QueuedFile } from "./_components/FileList";
import Results from "./_components/Results";

const AI_TYPES = new Set(["Approval Letter", "Purchase Contract"]);

const MAX_BYTES = 40 * 1024 * 1024;

// Same wording as the Streamlit scanner (DATA_HANDLING_NOTICE and render_compliance_statement).
const PRIVACY_TEXT = [
  "We never store your documents. We only save the loan details extracted from them so you don't have to re-scan.",
  "Uploaded documents are processed in memory only. Extracted loan details and scan history are saved in Supabase and tied to your account.",
  "Google does not use your data to train its models when you use a paid-tier Gemini API key.",
];

async function sha256(file: File): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
}

function isPdf(file: File): boolean {
  return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
}

export default function ScannerPage() {
  const [items, setItems] = useState<QueuedFile[]>([]);
  const [notices, setNotices] = useState<string[]>([]);
  const [needsKey, setNeedsKey] = useState(false);
  const [hasKey, setHasKey] = useState(false);
  const [batches, setBatches] = useState<ScanBatch[]>([]);
  const [progress, setProgress] = useState<string | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);
  const [usage, setUsage] = useState<UsageSummary | null>(null);

  useEffect(() => {
    // Until /api/me exists (T-13) this fails quietly and the key banner stays hidden.
    getMe()
      .then((me) => { setNeedsKey(!me.sandbox && !me.ai.has_key); setHasKey(me.ai.has_key); setUsage(me.usage); })
      .catch(() => setNeedsKey(false));
  }, []);

  const scanSelected = async () => {
    const queue = items.filter((it) => it.status === "ready" && it.checked);
    if (!queue.length || progress) return;
    setScanError(null);
    for (const [index, item] of queue.entries()) {
      if (item.type === "Unknown") {
        patch(item.id, { status: "error", checked: false, error: "Choose a document type, then scan again." });
        continue;
      }
      setProgress(
        hasKey && AI_TYPES.has(item.type)
          ? `Scanning ${index + 1} of ${queue.length}: ${item.file.name}. Sending redacted text to Gemini…`
          : `Scanning ${index + 1} of ${queue.length}: ${item.file.name}…`,
      );
      try {
        const response = await scanFile(item.file, item.type);
        const { usage: newUsage, ...batch } = response;
        if (newUsage) setUsage(newUsage);
        setBatches((list) => [batch, ...list]);
        setItems((list) => list.filter((it) => it.id !== item.id));
      } catch (err) {
        if (err instanceof ApiError && err.status === 402) {
          setScanError(`${err.message} The remaining files were not scanned.`);
          break;
        }
        patch(item.id, { status: "error", checked: false, error: err instanceof ApiError ? err.message : "Could not reach the server. Try again." });
      }
    }
    setProgress(null);
  };

  const patch = (id: string, change: Partial<QueuedFile>) =>
    setItems((list) => list.map((it) => (it.id === id ? { ...it, ...change } : it)));

  const addFiles = async (files: File[]) => {
    const messages: string[] = [];
    const known = new Set(items.map((it) => it.hash));
    const fresh: QueuedFile[] = [];

    for (const file of files) {
      if (!isPdf(file)) { messages.push(`${file.name} is not a PDF and was skipped.`); continue; }
      if (file.size > MAX_BYTES) { messages.push(`${file.name} is over the 40 MB limit and was skipped.`); continue; }
      const hash = await sha256(file);
      if (known.has(hash)) { messages.push(`${file.name} is identical to a file already in the list and was skipped.`); continue; }
      known.add(hash);
      fresh.push({ id: crypto.randomUUID(), file, hash, status: "detecting", type: "Unknown", confidence: null, checked: true });
    }

    setNotices(messages);
    if (!fresh.length) return;
    setItems((list) => [...list, ...fresh]);

    try {
      const { files: found } = await detectFiles(fresh.map((it) => it.file));
      setItems((list) => list.map((it) => {
        const index = fresh.findIndex((f) => f.id === it.id);
        if (index < 0 || !found[index]) return it;
        return { ...it, status: "ready", type: found[index].detected_type, confidence: found[index].confidence };
      }));
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Could not reach the server. Try again.";
      const ids = new Set(fresh.map((f) => f.id));
      setItems((list) => list.map((it) => (ids.has(it.id) ? { ...it, status: "error", checked: false, error: message } : it)));
    }
  };

  const remove = (id: string) => setItems((list) => list.filter((it) => it.id !== id));
  const setAll = (checked: boolean) => setItems((list) => list.map((it) => (it.status === "ready" ? { ...it, checked } : it)));
  const removeUnchecked = () => setItems((list) => list.filter((it) => it.checked));

  const selected = items.filter((it) => it.status === "ready" && it.checked);
  const detecting = items.some((it) => it.status === "detecting");
  const bulkActions: [string, () => void][] = [
    ["Check all", () => setAll(true)],
    ["Uncheck all", () => setAll(false)],
    ["Remove unchecked", removeUnchecked],
  ];

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 md:px-8 md:py-10">
      <div className="flex items-start gap-4">
        <div className="hidden size-11 shrink-0 place-items-center rounded-xl bg-brand-soft text-brand sm:grid">
          <ScanLine className="size-6" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Scan documents</h1>
          <p className="mt-1 text-sm text-muted">Upload loan PDFs to identify document types and match your pipeline.</p>
        </div>
      </div>

      {needsKey && (
        <div className="mt-6 flex flex-col gap-4 rounded-2xl border border-amber-500/30 bg-amber-500/[0.07] p-5 sm:flex-row sm:items-center">
          <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-amber-500/15 text-amber-600 dark:text-amber-400">
            <KeyRound className="size-5" />
          </div>
          <div className="flex-1">
            <p className="font-medium text-foreground">Add your Gemini API key to start scanning</p>
            <p className="mt-0.5 text-sm text-muted">
              The scanner uses Gemini 2.5 Flash to read your documents. Enable Google AI billing, then add your paid-tier API key. It takes about 60 seconds.
            </p>
          </div>
          <Link href="/settings/ai" className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-xl bg-brand px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-brand-strong">
            Set up key <ChevronRight className="size-4" />
          </Link>
        </div>
      )}

      <div className="mt-6">
        <Dropzone onFiles={(files) => void addFiles(files)} compact={items.length > 0} />
      </div>

      {notices.length > 0 && (
        <div className="mt-4 space-y-1 rounded-xl border border-amber-500/30 bg-amber-500/[0.07] px-4 py-3 text-sm text-foreground">
          {notices.map((n) => (
            <p key={n} className="flex items-start gap-2"><AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" />{n}</p>
          ))}
        </div>
      )}

      {items.length > 0 && (
        <section className="mt-6 overflow-hidden rounded-2xl border border-border bg-card shadow-card">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-3.5">
            <h2 className="text-sm font-semibold text-foreground">
              Documents <span className="ml-1 rounded-full bg-subtle px-2 py-0.5 text-xs font-medium text-muted">{items.length}</span>
            </h2>
            {items.length >= 2 && (
              <div className="flex flex-wrap gap-1.5">
                {bulkActions.map(([label, action]) => (
                  <button
                    key={label}
                    type="button"
                    onClick={action}
                    className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-muted transition hover:bg-subtle hover:text-foreground"
                  >
                    {label}
                  </button>
                ))}
              </div>
            )}
          </div>

          <FileList items={items} onChange={patch} onRemove={remove} />

          <div className="flex flex-col gap-3 border-t border-border bg-subtle/60 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0 text-xs text-muted">
              {progress ? (
                <p className="flex items-center gap-2 text-foreground"><Loader2 className="size-4 shrink-0 animate-spin text-brand" /><span className="truncate">{progress}</span></p>
              ) : detecting ? (
                <p>Detecting document types…</p>
              ) : (
                <p>Check the detected types, then scan. Documents stay on our server and are never stored.</p>
              )}
              {usage && usage.limit !== null && !progress && (
                <p className="mt-1">{usage.tier_name} plan: {usage.used} of {usage.limit} scans used this month ({usage.remaining} left)</p>
              )}
            </div>
            <button
              type="button"
              onClick={() => void scanSelected()}
              disabled={!selected.length || detecting || progress !== null}
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-brand px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-brand-strong disabled:cursor-not-allowed disabled:opacity-50"
            >
              {progress ? <Loader2 className="size-4 animate-spin" /> : <ScanLine className="size-4" />}
              Scan ({selected.length} selected)
            </button>
          </div>
        </section>
      )}

      {scanError && (
        <div className="mt-4 flex items-start gap-3 rounded-xl border border-rose-500/30 bg-rose-500/[0.07] px-4 py-3 text-sm text-foreground">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-rose-600" />
          <p className="flex-1">{scanError}</p>
          <Link href="/pricing" className="shrink-0 font-medium text-brand hover:underline">See plans</Link>
        </div>
      )}

      <Results batches={batches} />

      <div className="mt-6 grid gap-4 md:grid-cols-[1fr_auto]">
        <details className="group rounded-2xl border border-border bg-card shadow-card">
          <summary className="flex cursor-pointer list-none items-center gap-3 px-5 py-4 text-sm font-medium text-foreground [&::-webkit-details-marker]:hidden">
            <ShieldCheck className="size-5 text-brand" />
            <span className="flex-1">Privacy and data handling</span>
            <ChevronRight className="size-4 text-muted transition-transform group-open:rotate-90" />
          </summary>
          <div className="space-y-2 border-t border-border px-5 py-4 text-sm leading-relaxed text-muted">
            {PRIVACY_TEXT.map((p) => <p key={p}>{p}</p>)}
            <p><Link href="/privacy" className="font-medium text-brand hover:underline">Read the full Privacy Policy</Link></p>
          </div>
        </details>

        <Link
          href="/pipeline?import=1"
          className="flex items-center gap-3 rounded-2xl border border-border bg-card px-5 py-4 text-sm font-medium text-foreground shadow-card transition hover:border-brand/40 md:self-start"
        >
          <FileSpreadsheet className="size-5 text-brand" />
          Import pipeline spreadsheet
          <ChevronRight className="size-4 text-muted" />
        </Link>
      </div>
    </div>
  );
}

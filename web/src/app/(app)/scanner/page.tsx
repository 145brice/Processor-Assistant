"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle, ArrowRight, KeyRound, Loader2, Lock, ScanLine, X } from "lucide-react";
import { ApiError, detectFiles, getMe, scanFile } from "@/lib/api";
import type { ScanBatch, UsageSummary } from "@/lib/types";
import Dropzone from "./_components/Dropzone";
import FileList, { type QueuedFile } from "./_components/FileList";
import Results from "./_components/Results";
import SideRail from "./_components/SideRail";
import Steps from "./_components/Steps";

const MAX_BYTES = 40 * 1024 * 1024;
const AI_TYPES = new Set(["Approval Letter", "Purchase Contract"]);

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
  const [progress, setProgress] = useState<{ index: number; total: number; text: string } | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);
  const [usage, setUsage] = useState<UsageSummary | null>(null);

  useEffect(() => {
    // If /api/me fails, the key banner stays hidden rather than nagging.
    const load = () =>
      getMe()
        .then((me) => { setNeedsKey(!me.sandbox && !me.ai.has_key); setHasKey(me.ai.has_key); setUsage(me.usage); })
        .catch(() => setNeedsKey(false));
    void load();
    // The setup wizard announces a saved key so the banner can go away without a reload.
    window.addEventListener("pa:ai-key-saved", load);
    return () => window.removeEventListener("pa:ai-key-saved", load);
  }, []);

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

  const scanSelected = async () => {
    const queue = items.filter((it) => it.status === "ready" && it.checked);
    if (!queue.length || progress) return;
    setScanError(null);
    for (const [index, item] of queue.entries()) {
      if (item.type === "Unknown") {
        patch(item.id, { status: "error", checked: false, error: "Choose a document type, then scan again." });
        continue;
      }
      setProgress({
        index, total: queue.length,
        text: hasKey && AI_TYPES.has(item.type)
          ? `${item.file.name}: sending redacted text to Gemini…`
          : `${item.file.name}: reading document…`,
      });
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

  const remove = (id: string) => setItems((list) => list.filter((it) => it.id !== id));
  const setAll = (checked: boolean) => setItems((list) => list.map((it) => (it.status === "ready" ? { ...it, checked } : it)));
  const removeUnchecked = () => setItems((list) => list.filter((it) => it.checked));

  const selected = items.filter((it) => it.status === "ready" && it.checked);
  const detecting = items.some((it) => it.status === "detecting");
  const step = progress ? 2 : items.length ? 1 : batches.length ? 3 : 0;
  const bulkActions: [string, () => void][] = [
    ["Check all", () => setAll(true)],
    ["Uncheck all", () => setAll(false)],
    ["Remove unchecked", removeUnchecked],
  ];

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 md:px-8 md:py-10">
      {/* Page header */}
      <header className="flex flex-col gap-5 border-b border-border pb-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-muted">
            <ScanLine className="size-3.5 text-brand" /> Scanner
          </div>
          <h1 className="mt-2 text-[28px] font-semibold leading-tight tracking-[-0.02em] text-foreground">Scan documents</h1>
          <p className="mt-1.5 max-w-xl text-sm text-muted">Upload loan PDFs to identify document types and match your pipeline.</p>
        </div>
        <div className="flex flex-col items-start gap-3 lg:items-end">
          <Steps current={step} />
          <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1 text-[11px] font-medium text-muted shadow-card">
            <Lock className="size-3 text-emerald-600" /> Processed in memory · never stored
          </span>
        </div>
      </header>

      <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="min-w-0 space-y-5">
          {needsKey && (
            <div className="animate-fade-up flex flex-col gap-4 rounded-2xl border border-amber-500/25 bg-gradient-to-r from-amber-500/[0.09] to-transparent p-5 sm:flex-row sm:items-center">
              <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-amber-500/15 text-amber-600 dark:text-amber-400">
                <KeyRound className="size-5" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-foreground">Add your Gemini API key to start scanning</p>
                <p className="mt-0.5 text-[13px] text-muted">
                  The scanner uses Gemini 2.5 Flash to read your documents. Enable Google AI billing, then add your paid-tier API key. It takes about 60 seconds.
                </p>
              </div>
              <button
                type="button"
                onClick={() => window.dispatchEvent(new Event("pa:open-gemini-setup"))}
                className="group inline-flex shrink-0 items-center justify-center gap-1.5 rounded-xl bg-foreground px-4 py-2.5 text-sm font-medium text-background transition hover:opacity-90"
              >
                Set up key <ArrowRight className="size-4 transition group-hover:translate-x-0.5" />
              </button>
            </div>
          )}

          <Dropzone onFiles={(files) => void addFiles(files)} compact={items.length > 0 || batches.length > 0} />

          {notices.length > 0 && (
            <div className="animate-fade-up flex items-start gap-3 rounded-xl border border-amber-500/25 bg-amber-500/[0.07] px-4 py-3 text-[13px] text-foreground">
              <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" />
              <div className="flex-1 space-y-0.5">{notices.map((n) => <p key={n}>{n}</p>)}</div>
              <button type="button" onClick={() => setNotices([])} aria-label="Dismiss" className="text-muted hover:text-foreground"><X className="size-4" /></button>
            </div>
          )}

          {items.length > 0 && (
            <section className="animate-fade-up overflow-hidden rounded-2xl border border-border bg-card shadow-card">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-3">
                <h2 className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  Documents
                  <span className="rounded-md bg-subtle px-1.5 py-0.5 text-[11px] font-medium tabular-nums text-muted">{items.length}</span>
                </h2>
                {items.length >= 2 && (
                  <div className="flex flex-wrap gap-1">
                    {bulkActions.map(([label, action]) => (
                      <button key={label} type="button" onClick={action}
                        className="rounded-md px-2 py-1 text-xs font-medium text-muted transition hover:bg-subtle hover:text-foreground">
                        {label}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <FileList items={items} onChange={patch} onRemove={remove} />

              <div className="border-t border-border bg-subtle/50">
                {progress && (
                  <div className="h-0.5 bg-border">
                    <div className="h-full bg-brand transition-all duration-500" style={{ width: `${((progress.index + 0.5) / progress.total) * 100}%` }} />
                  </div>
                )}
                <div className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0 text-xs text-muted">
                    {progress ? (
                      <p className="flex items-center gap-2 text-foreground">
                        <Loader2 className="size-4 shrink-0 animate-spin text-brand" />
                        <span className="tabular-nums text-muted">{progress.index + 1}/{progress.total}</span>
                        <span className="truncate">{progress.text}</span>
                      </p>
                    ) : detecting ? (
                      <p className="flex items-center gap-2"><Loader2 className="size-3.5 animate-spin" />Detecting document types…</p>
                    ) : (
                      <p>Check the detected types, then scan.</p>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => void scanSelected()}
                    disabled={!selected.length || detecting || progress !== null}
                    className="group inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-brand px-5 py-2.5 text-sm font-medium text-white shadow-md shadow-brand/20 transition hover:-translate-y-px hover:bg-brand-strong hover:shadow-lg hover:shadow-brand/25 active:translate-y-0 disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none"
                  >
                    {progress ? <Loader2 className="size-4 animate-spin" /> : <ScanLine className="size-4" />}
                    Scan {selected.length} {selected.length === 1 ? "document" : "documents"}
                  </button>
                </div>
              </div>
            </section>
          )}

          {scanError && (
            <div className="animate-fade-up flex items-start gap-3 rounded-xl border border-rose-500/25 bg-rose-500/[0.07] px-4 py-3 text-[13px] text-foreground">
              <AlertTriangle className="mt-0.5 size-4 shrink-0 text-rose-600" />
              <p className="flex-1">{scanError}</p>
              <Link href="/pricing" className="shrink-0 font-medium text-brand hover:underline">See plans</Link>
            </div>
          )}

          <Results batches={batches} />
        </div>

        <SideRail usage={usage} />
      </div>
    </div>
  );
}

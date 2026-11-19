"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FileClock, Loader2, RotateCcw, Trash2 } from "lucide-react";
import { ApiError, deleteScan, listScans } from "@/lib/api";
import type { SavedScan } from "@/lib/types";

/** The scanner picks this up on load and shows the saved scan in its results. */
export const RESTORE_KEY = "pa_restore_scan";

export default function HistoryPage() {
  const router = useRouter();
  const [items, setItems] = useState<SavedScan[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    listScans()
      .then((r) => setItems(r.items))
      .catch((e) =>
        setError(
          e instanceof ApiError ? e.message : "Could not load saved scans.",
        ),
      );
  }, []);

  async function remove(id: string) {
    setError("");
    try {
      await deleteScan(id);
      setItems((current) => current?.filter((item) => item.id !== id) ?? []);
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Could not delete that scan.",
      );
    }
  }

  function restore(item: SavedScan) {
    try {
      window.sessionStorage.setItem(RESTORE_KEY, JSON.stringify(item.batch));
    } catch {
      setError("Your browser blocked restoring this scan.");
      return;
    }
    router.push("/scanner");
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 md:px-8">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">
        History
      </p>
      <h1 className="mt-2 text-[28px] font-semibold text-foreground">
        Saved scans
      </h1>
      {error && <p className="mt-6 text-sm text-rose-600">{error}</p>}
      {items === null && !error && (
        <div className="mt-8 flex items-center gap-2 text-muted">
          <Loader2 className="size-5 animate-spin" /> Loading saved scans…
        </div>
      )}
      {items?.length === 0 && (
        <div className="mt-8 rounded-2xl border border-border bg-card p-10 text-center shadow-card">
          <FileClock className="mx-auto size-9 text-muted" />
          <p className="mt-3 text-foreground">No saved scans yet.</p>
          <p className="mt-1 text-sm text-muted">
            Completed scans will appear here for quick reference.
          </p>
        </div>
      )}
      <div className="mt-8 grid gap-4">
        {items?.map((item) => (
          <article
            key={item.id}
            className="flex items-center justify-between gap-4 rounded-2xl border border-border bg-card p-5 shadow-card"
          >
            <div className="min-w-0">
              <p className="truncate font-medium text-foreground">
                {item.batch.file}
              </p>
              <p className="mt-1 text-sm text-muted">
                {new Date(item.saved_at).toLocaleString()}
              </p>
              <p className="mt-1 text-sm text-muted">{item.batch.type}</p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <button
                type="button"
                onClick={() => restore(item)}
                className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-card px-3 py-2 text-sm font-medium text-foreground shadow-card transition hover:border-brand/40 hover:bg-subtle"
              >
                <RotateCcw className="size-4" /> Restore
              </button>
              <button
                type="button"
                onClick={() => void remove(item.id)}
                className="rounded-xl border border-border p-2 text-muted hover:text-rose-600"
                aria-label="Delete saved scan"
              >
                <Trash2 className="size-4" />
              </button>
            </div>
          </article>
        ))}
      </div>
    </main>
  );
}

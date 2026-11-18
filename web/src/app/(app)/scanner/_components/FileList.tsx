"use client";

import { AlertCircle, FileText, Loader2, X } from "lucide-react";
import { DOC_TYPES, type DocType } from "@/lib/types";

export interface QueuedFile {
  id: string;
  file: File;
  hash: string;
  status: "detecting" | "ready" | "error";
  type: DocType;
  confidence: "High" | "Medium" | "Low" | null;
  checked: boolean;
  error?: string;
}

const CONFIDENCE_STYLE: Record<string, string> = {
  High: "bg-emerald-500/10 text-emerald-700 ring-emerald-500/20 dark:text-emerald-300",
  Medium: "bg-amber-500/10 text-amber-700 ring-amber-500/25 dark:text-amber-300",
  Low: "bg-subtle text-muted ring-border",
};

export function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileList({ items, onChange, onRemove }: {
  items: QueuedFile[];
  onChange: (id: string, patch: Partial<QueuedFile>) => void;
  onRemove: (id: string) => void;
}) {
  return (
    <ul className="divide-y divide-border">
      {items.map((item) => (
        <li key={item.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-5 py-3.5 sm:flex-nowrap">
          <input
            type="checkbox"
            aria-label={`Include ${item.file.name}`}
            checked={item.checked}
            disabled={item.status !== "ready"}
            onChange={(e) => onChange(item.id, { checked: e.target.checked })}
            className="size-4 shrink-0 rounded accent-brand disabled:opacity-40"
          />
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <div className={"grid size-9 shrink-0 place-items-center rounded-lg " + (item.status === "error" ? "bg-rose-500/10 text-rose-600" : "bg-subtle text-muted")}>
              {item.status === "error" ? <AlertCircle className="size-4" /> : <FileText className="size-4" />}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-foreground" title={item.file.name}>{item.file.name}</p>
              <p className={"text-xs " + (item.status === "error" ? "text-rose-600 dark:text-rose-400" : "text-muted")}>
                {item.status === "error" ? item.error : formatSize(item.file.size)}
              </p>
            </div>
          </div>

          {item.status === "detecting" && (
            <span className="ml-8 inline-flex items-center gap-2 text-sm text-muted sm:ml-0">
              <Loader2 className="size-4 animate-spin" /> Detecting type…
            </span>
          )}

          {item.status === "ready" && (
            <div className="ml-8 flex items-center gap-3 sm:ml-0">
              <select
                aria-label={`Document type for ${item.file.name}`}
                value={item.type}
                onChange={(e) => onChange(item.id, { type: e.target.value as DocType })}
                className="h-9 w-56 rounded-lg border border-border bg-card px-2.5 text-sm text-foreground shadow-card focus:border-brand focus:outline-none"
              >
                {DOC_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
              {item.confidence && (
                <span
                  title="How sure the automatic detection is"
                  className={"w-16 rounded-full px-2 py-0.5 text-center text-xs font-medium ring-1 ring-inset " + CONFIDENCE_STYLE[item.confidence]}
                >
                  {item.confidence}
                </span>
              )}
            </div>
          )}

          <button
            type="button"
            onClick={() => onRemove(item.id)}
            aria-label={`Remove ${item.file.name}`}
            className="grid size-8 shrink-0 place-items-center rounded-lg text-muted transition hover:bg-subtle hover:text-foreground"
          >
            <X className="size-4" />
          </button>
        </li>
      ))}
    </ul>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listLoans } from "@/lib/api";
import type { StatusCounts } from "@/lib/types";

const CHIPS: { label: string; key: keyof StatusCounts; status?: string; dot: string }[] = [
  { label: "All", key: "all", dot: "bg-slate-400" },
  { label: "Pending UW", key: "pending", status: "Pending", dot: "bg-amber-400" },
  { label: "Requested", key: "requested", status: "Requested", dot: "bg-sky-500" },
  { label: "Cleared", key: "cleared", status: "Cleared", dot: "bg-emerald-500" },
  { label: "Overdue", key: "overdue", status: "Overdue", dot: "bg-rose-500" },
  { label: "Closed", key: "closed", status: "Closed", dot: "bg-slate-500" },
];

export default function Header() {
  // null until real counts arrive; we never show a made-up 0.
  const [counts, setCounts] = useState<StatusCounts | null>(null);
  useEffect(() => { listLoans().then((result) => setCounts(result.counts)).catch(() => setCounts(null)); }, []);
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-surface/85 backdrop-blur supports-[backdrop-filter]:bg-surface/70">
      <div className="flex items-center gap-4 px-4 py-3 pl-16 md:px-8">
        <span className="hidden shrink-0 text-xs font-semibold uppercase tracking-[0.08em] text-muted sm:block">My pipeline</span>
        <div className="-my-1 flex min-w-0 flex-1 gap-2 overflow-x-auto py-1 [scrollbar-width:none]">
          {CHIPS.map((chip) => (
            <Link
              key={chip.label}
              href={chip.status ? "/pipeline?status=" + chip.status : "/pipeline"}
              className="inline-flex shrink-0 items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-sm font-medium text-foreground/80 shadow-card transition hover:border-brand/40 hover:text-foreground"
            >
              <span className={"size-2 rounded-full " + chip.dot} />
              {chip.label}
              {counts && (
                <span className="rounded-full bg-subtle px-1.5 text-xs font-semibold tabular-nums text-muted">{counts[chip.key]}</span>
              )}
            </Link>
          ))}
        </div>
      </div>
    </header>
  );
}

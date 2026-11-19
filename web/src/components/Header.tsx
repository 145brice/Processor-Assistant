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
      <div className="flex h-14 items-center gap-4 px-4 pl-16 md:px-8">
        <span className="hidden shrink-0 text-[11px] font-semibold uppercase tracking-[0.1em] text-muted sm:block">My pipeline</span>
        <div className="min-w-0 overflow-x-auto [scrollbar-width:none]">
          <div className="inline-flex items-center gap-0.5 rounded-xl border border-border bg-subtle/70 p-0.5">
            {CHIPS.map((chip) => (
              <Link
                key={chip.label}
                href={chip.status ? "/pipeline?status=" + chip.status : "/pipeline"}
                className="inline-flex h-7 shrink-0 items-center gap-1.5 rounded-[10px] px-2.5 text-[13px] font-medium text-muted transition hover:bg-card hover:text-foreground hover:shadow-card"
              >
                <span className={"size-1.5 rounded-full " + chip.dot} />
                {chip.label}
                {counts && <span className="tabular-nums text-foreground/70">{counts[chip.key]}</span>}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </header>
  );
}

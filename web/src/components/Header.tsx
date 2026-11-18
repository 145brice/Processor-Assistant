"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listLoans } from "@/lib/api";
import type { StatusCounts } from "@/lib/types";

const CHIPS: { label: string; key: keyof StatusCounts; status?: string }[] = [
  { label: "All", key: "all" },
  { label: "Pending UW", key: "pending", status: "Pending" },
  { label: "Requested", key: "requested", status: "Requested" },
  { label: "Cleared", key: "cleared", status: "Cleared" },
  { label: "Overdue", key: "overdue", status: "Overdue" },
  { label: "Closed", key: "closed", status: "Closed" },
];

export default function Header() {
  const [counts, setCounts] = useState<StatusCounts | null>(null);
  useEffect(() => { listLoans().then((result) => setCounts(result.counts)).catch(() => setCounts(null)); }, []);
  return (
    <header className="flex flex-wrap items-center gap-2 border-b border-[var(--border)] bg-[var(--surface)] px-4 py-3 pl-16 md:pl-4">
      <span className="mr-2 text-sm font-bold tracking-widest text-[var(--muted)]">MY PIPELINE</span>
      {CHIPS.map((chip) => (
        <Link key={chip.label} href={chip.status ? "/pipeline?status=" + chip.status : "/pipeline"} className="rounded border border-[var(--border)] bg-[var(--card)] px-2 py-1 text-sm text-[var(--muted)] hover:border-[#4368b8]">
          {counts ? counts[chip.key] : "–"} {chip.label}
        </Link>
      ))}
    </header>
  );
}

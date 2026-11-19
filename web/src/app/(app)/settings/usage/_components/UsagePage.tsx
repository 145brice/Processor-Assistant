"use client";
import { useEffect, useState } from "react";
import { BarChart3, Loader2 } from "lucide-react";
import { ApiError, getUsage } from "@/lib/api";
import type { UsageSummary } from "@/lib/types";
export default function UsagePage() {
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    getUsage()
      .then(setUsage)
      .catch((e) =>
        setError(e instanceof ApiError ? e.message : "Could not load usage."),
      );
  }, []);
  return (
    <main className="mx-auto max-w-3xl px-4 py-8 md:px-8">
      <p className="text-xs font-semibold uppercase tracking-[.12em] text-muted">
        Settings
      </p>
      <h1 className="mt-2 text-[28px] font-semibold text-foreground">
        Usage & billing
      </h1>
      <section className="mt-8 rounded-2xl border border-border bg-card p-6 shadow-card">
        <BarChart3 className="size-6 text-brand" />
        {!usage && !error && (
          <Loader2 className="mt-6 size-5 animate-spin text-muted" />
        )}
        {error && <p className="mt-5 text-sm text-rose-600">{error}</p>}
        {usage && (
          <>
            <p className="mt-5 text-sm text-muted">{usage.tier_name}</p>
            <div className="mt-4 h-3 overflow-hidden rounded-full bg-subtle">
              <div
                className="h-full rounded-full bg-brand"
                style={{
                  width: usage.limit
                    ? Math.min(100, (usage.used / usage.limit) * 100) + "%"
                    : "0%",
                }}
              />
            </div>
            <p className="mt-3 text-sm text-muted">
              {usage.used} scans used
              {usage.limit === null ? "" : " of " + usage.limit}.{" "}
              {usage.free_beta ? "Beta access included." : ""}
            </p>
          </>
        )}
      </section>
    </main>
  );
}

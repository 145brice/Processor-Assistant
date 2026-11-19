"use client";
import { useEffect, useState } from "react";
import { CheckCircle2, Circle, ClipboardCheck, Loader2 } from "lucide-react";
import { getMe } from "@/lib/api";
import type { Me } from "@/lib/types";
export default function OverviewPage() {
  const [me, setMe] = useState<Me | null>(null);
  useEffect(() => {
    getMe()
      .then(setMe)
      .catch(() => undefined);
  }, []);
  const checks = me
    ? [
        {
          label: "Accept the privacy terms",
          done: me.terms_accepted,
          href: "/terms",
        },
        {
          label: "Add your Gemini API key",
          done: me.ai.has_key,
          href: "/settings/ai",
        },
        { label: "Run your first scan", done: false, href: "/scanner" },
      ]
    : [];
  return (
    <main className="mx-auto max-w-3xl px-4 py-8 md:px-8">
      <p className="text-xs font-semibold uppercase tracking-[.12em] text-muted">
        Getting started
      </p>
      <h1 className="mt-2 text-[28px] font-semibold text-foreground">
        Overview
      </h1>
      <section className="mt-8 rounded-2xl border border-border bg-card p-6 shadow-card">
        <ClipboardCheck className="size-6 text-brand" />
        <h2 className="mt-4 text-xl font-semibold text-foreground">
          Set up Processor Assistant
        </h2>
        <p className="mt-2 text-muted">
          Complete these steps to start processing loan documents.
        </p>
        {!me && <Loader2 className="mt-6 size-5 animate-spin text-muted" />}
        {me && (
          <div className="mt-6 space-y-3">
            {checks.map((i) => (
              <a
                key={i.label}
                href={i.href}
                className="flex items-center gap-3 rounded-xl border border-border p-3"
              >
                {i.done ? (
                  <CheckCircle2 className="size-5 text-emerald-600" />
                ) : (
                  <Circle className="size-5 text-muted" />
                )}
                <span className="text-sm text-foreground">{i.label}</span>
              </a>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

"use client";
import { useEffect, useState } from "react";
import { Check, Loader2, Sparkles } from "lucide-react";
import { ApiError, getPricing } from "@/lib/api";
import type { Pricing } from "@/lib/types";
export default function Page() {
  const [pricing, setPricing] = useState<Pricing | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    getPricing()
      .then(setPricing)
      .catch((e) =>
        setError(e instanceof ApiError ? e.message : "Could not load pricing."),
      );
  }, []);
  return (
    <main className="mx-auto max-w-5xl px-4 py-8 md:px-8">
      <p className="text-xs font-semibold uppercase tracking-[.12em] text-muted">
        Plans
      </p>
      <h1 className="mt-2 text-[28px] font-semibold text-foreground">
        Pricing
      </h1>
      <p className="mt-3 text-muted">
        Simple plans for processing loan documents every month.
      </p>
      {error && <p className="mt-6 text-sm text-rose-600">{error}</p>}
      {!pricing && !error && (
        <Loader2 className="mt-8 size-5 animate-spin text-muted" />
      )}
      {pricing && (
        <>
          <p className="mt-6 rounded-xl bg-brand-soft p-4 text-sm text-brand">
            {pricing.beta_offer}
          </p>
          <div className="mt-8 grid gap-4 md:grid-cols-4">
            {pricing.tiers.map((t) => (
              <article
                key={t.key}
                className="rounded-2xl border border-border bg-card p-5 shadow-card"
              >
                <Sparkles className="size-5 text-brand" />
                <h2 className="mt-4 font-semibold text-foreground">{t.name}</h2>
                <p className="mt-2 text-2xl font-semibold text-foreground">
                  {"$"}
                  {t.price}
                </p>
                <p className="mt-3 text-sm text-muted">
                  {t.scan_limit === null
                    ? "Unlimited scans"
                    : t.scan_limit + " scans per month"}
                </p>
                <p className="mt-5 flex items-center gap-2 text-sm text-muted">
                  <Check className="size-4 text-emerald-600" /> Secure
                  processing
                </p>
                {t.payment_link && (
                  <a
                    href={t.payment_link}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-5 inline-block rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-white"
                  >
                    Choose plan
                  </a>
                )}
              </article>
            ))}
          </div>
        </>
      )}
    </main>
  );
}

import Link from "next/link";
import {
  ArrowUpRight,
  EyeOff,
  FileSpreadsheet,
  FileText,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { UsageSummary } from "@/lib/types";

const HOW = [
  {
    icon: FileText,
    title: "Read on our server",
    text: "Text is pulled from your PDF in memory. The file is never stored.",
  },
  {
    icon: EyeOff,
    title: "Personal details removed",
    text: "Names, SSNs, phones and addresses are redacted before any AI sees the text.",
  },
  {
    icon: Sparkles,
    title: "AI with your own key",
    text: "Approval letters and contracts are enhanced by Gemini using your key only.",
  },
];

function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={"border-b border-border/70 py-5 last:border-b-0 " + className}
    >
      {children}
    </section>
  );
}

export default function SideRail({ usage }: { usage: UsageSummary | null }) {
  const limited = usage && usage.limit !== null;
  const pct = limited
    ? Math.min(
        100,
        Math.round((usage.used / Math.max(1, usage.limit ?? 1)) * 100),
      )
    : 0;

  return (
    <aside className="overflow-hidden rounded-[24px] bg-card/80 px-5 shadow-[0_20px_55px_-42px_rgba(15,23,42,0.55)] ring-1 ring-black/[0.04] dark:ring-white/[0.07]">
      {usage && (
        <Card>
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
              This month
            </p>
            <span className="rounded-full bg-brand-soft px-2 py-0.5 text-[11px] font-medium text-brand">
              {usage.tier_name}
            </span>
          </div>
          {limited ? (
            <>
              <p className="mt-3 text-2xl font-semibold tabular-nums tracking-tight text-foreground">
                {usage.used}
                <span className="text-base font-medium text-muted">
                  {" "}
                  / {usage.limit} scans
                </span>
              </p>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-subtle">
                <div
                  className={
                    "h-full rounded-full transition-all " +
                    (pct >= 90
                      ? "bg-rose-500"
                      : pct >= 70
                        ? "bg-amber-500"
                        : "bg-brand")
                  }
                  style={{ width: `${pct}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-muted">
                {usage.remaining} left this month
              </p>
            </>
          ) : (
            <p className="mt-3 text-sm text-foreground">Unlimited scans</p>
          )}
        </Card>
      )}

      <Card>
        <div className="flex items-center gap-2">
          <ShieldCheck className="size-4 text-brand" />
          <p className="text-sm font-semibold text-foreground">
            How your documents are handled
          </p>
        </div>
        <ol className="mt-4 space-y-4">
          {HOW.map(({ icon: Icon, title, text }, i) => (
            <li key={title} className="relative flex gap-3">
              {i < HOW.length - 1 && (
                <span className="absolute left-[15px] top-9 h-[calc(100%-12px)] w-px bg-border" />
              )}
              <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-subtle text-foreground/70 ring-1 ring-border">
                <Icon className="size-4" />
              </span>
              <div>
                <p className="text-[13px] font-medium text-foreground">
                  {title}
                </p>
                <p className="mt-0.5 text-xs leading-relaxed text-muted">
                  {text}
                </p>
              </div>
            </li>
          ))}
        </ol>
        <Link
          href="/privacy"
          className="mt-4 inline-flex items-center gap-1 text-xs font-medium text-brand hover:underline"
        >
          Privacy policy <ArrowUpRight className="size-3" />
        </Link>
      </Card>

      <Link
        href="/pipeline?import=1"
        className="group flex items-center gap-3 py-5 transition hover:text-brand"
      >
        <span className="grid size-9 place-items-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
          <FileSpreadsheet className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[13px] font-medium text-foreground">
            Import pipeline spreadsheet
          </p>
          <p className="text-xs text-muted">
            Bring in loans from a CSV or JSON file
          </p>
        </div>
        <ArrowUpRight className="size-4 text-muted transition group-hover:text-brand" />
      </Link>
    </aside>
  );
}

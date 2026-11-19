"use client";

import Link from "next/link";
import { useState } from "react";
import { AlertTriangle, ArrowUpRight, Check, CheckCircle2, ClipboardCopy, Info, XCircle } from "lucide-react";
import type { Tone, ToolBlock } from "@/lib/tools";

const TONE_BOX: Record<Tone, string> = {
  good: "border-emerald-500/25 bg-emerald-500/[0.07] text-emerald-800 dark:text-emerald-300",
  warn: "border-amber-500/30 bg-amber-500/[0.08] text-amber-800 dark:text-amber-300",
  bad: "border-rose-500/25 bg-rose-500/[0.07] text-rose-800 dark:text-rose-300",
  info: "border-brand/25 bg-brand-soft text-foreground",
  neutral: "border-border bg-surface text-foreground",
};
const TONE_NUM: Record<Tone, string> = {
  good: "text-emerald-600",
  warn: "text-amber-600",
  bad: "text-rose-600",
  info: "text-brand",
  neutral: "text-foreground",
};

function Title({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">{children}</h3>
  );
}

function CopyText({ title, text }: { title: string; text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };
  return (
    <section>
      <div className="mb-2 flex items-center justify-between">
        <Title>{title}</Title>
        <button
          type="button"
          onClick={() => void copy()}
          className="-mt-2 inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium text-muted transition hover:bg-subtle hover:text-foreground"
        >
          {copied ? <Check className="size-3.5 text-emerald-600" /> : <ClipboardCopy className="size-3.5" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="whitespace-pre-wrap break-words rounded-xl border border-border bg-surface px-4 py-3 font-sans text-[13px] leading-relaxed text-foreground">
        {text}
      </pre>
    </section>
  );
}

function Block({ block }: { block: ToolBlock }) {
  switch (block.type) {
    case "stats":
      return (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {block.items.map((item) => (
            <div key={item.label} className="rounded-xl border border-border bg-card p-4 shadow-card">
              <p className={"text-2xl font-semibold tabular-nums " + TONE_NUM[item.tone]}>{item.value}</p>
              <p className="mt-1 text-xs text-muted">{item.label}</p>
            </div>
          ))}
        </div>
      );
    case "list":
      return (
        <section>
          <Title>{block.title}</Title>
          <ul className="space-y-1.5">
            {block.items.map((item) => (
              <li key={item} className={"rounded-lg border px-3 py-2 text-[13px] " + TONE_BOX[block.tone]}>
                {item}
              </li>
            ))}
          </ul>
        </section>
      );
    case "checklist":
      return (
        <section>
          <Title>{block.title}</Title>
          <ul className="divide-y divide-border overflow-hidden rounded-xl border border-border">
            {block.rows.map((row) => (
              <li key={row.label} className="flex items-center gap-3 px-4 py-2.5 text-sm">
                {row.ok ? (
                  <CheckCircle2 className="size-4 shrink-0 text-emerald-600" />
                ) : (
                  <XCircle className="size-4 shrink-0 text-rose-600" />
                )}
                <span className="flex-1 text-foreground">{row.label}</span>
                <span className={"text-xs font-medium " + (row.ok ? "text-emerald-600" : "text-rose-600")}>
                  {row.ok ? "Received" : "Missing"}
                </span>
              </li>
            ))}
          </ul>
        </section>
      );
    case "kv":
      return (
        <section>
          <Title>{block.title}</Title>
          <dl className="divide-y divide-border overflow-hidden rounded-xl border border-border">
            {block.rows.map((row) => (
              <div key={row.label} className="grid grid-cols-[minmax(0,2fr)_minmax(0,3fr)] gap-3 px-4 py-2 text-[13px]">
                <dt className="text-muted">{row.label}</dt>
                <dd className="break-words text-foreground">{row.value}</dd>
              </div>
            ))}
          </dl>
        </section>
      );
    case "text":
      return <CopyText title={block.title} text={block.text} />;
    case "notice": {
      const Icon = block.tone === "bad" ? XCircle : block.tone === "warn" ? AlertTriangle : block.tone === "good" ? CheckCircle2 : Info;
      return (
        <div className={"flex items-start gap-3 rounded-xl border px-4 py-3 text-[13px] " + TONE_BOX[block.tone]}>
          <Icon className="mt-0.5 size-4 shrink-0" />
          <p className="flex-1">{block.text}</p>
          {block.href && (
            <Link href={block.href} className="shrink-0 font-medium underline-offset-2 hover:underline">
              {block.link_label || "Open"}
            </Link>
          )}
        </div>
      );
    }
    case "table":
      return (
        <section>
          <Title>{block.title}</Title>
          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="w-full text-left text-[13px]">
              <thead className="bg-subtle text-xs text-muted">
                <tr>
                  {block.columns.map((c) => (
                    <th key={c} className="px-4 py-2 font-medium">{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {block.rows.map((row, i) => (
                  <tr key={i}>
                    {row.map((cell, j) => (
                      <td key={j} className="px-4 py-2 text-foreground">{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      );
    case "link":
      return (
        <a
          href={block.href}
          className="inline-flex w-fit items-center gap-2 rounded-xl bg-brand px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-brand-strong"
        >
          {block.label} <ArrowUpRight className="size-4" />
        </a>
      );
  }
}

export default function ToolBlocks({ blocks }: { blocks: ToolBlock[] }) {
  return (
    <div className="animate-fade-up space-y-5">
      {blocks.map((block, index) => (
        <Block key={index} block={block} />
      ))}
    </div>
  );
}

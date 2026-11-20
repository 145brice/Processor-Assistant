"use client";

import { useState } from "react";
import {
  Check,
  ClipboardCopy,
  Copy,
  FileDown,
  FileSpreadsheet,
  Loader2,
  Mail,
  Mailbox,
  Phone,
  UserRound,
} from "lucide-react";
import { ApiError, emailDrafts, exportCsv, exportPdf } from "@/lib/api";
import type { Contact, EmailDraft, EmailDrafts, ScanBatch } from "@/lib/types";

// ---------- helpers ----------
function humanize(key: string): string {
  return key
    .replace(/\[(\d+)\]/g, " $1")
    .split(".")
    .map((part) =>
      part.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase()),
    )
    .join(" › ");
}

/** Same flattening as scan_outputs.flattened_fields, so the table matches the CSV export. */
export function flattenFields(value: unknown, prefix = ""): [string, string][] {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return Object.entries(value as Record<string, unknown>).flatMap(([k, v]) =>
      flattenFields(v, prefix ? `${prefix}.${k}` : k),
    );
  }
  if (Array.isArray(value))
    return value.flatMap((v, i) => flattenFields(v, `${prefix}[${i + 1}]`));
  if (value === null || value === undefined || value === "") return [];
  return [[prefix, String(value)]];
}

function roleLabel(role: string): string {
  return role.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function borrowerOf(batch: ScanBatch): string {
  const contacts = batch.result.contacts;
  const role = Object.keys(contacts).find((r) => /borrower|buyer/i.test(r));
  return (role && contacts[role]?.name) || batch.loan_match.borrower || "";
}

export function summaryText(batch: ScanBatch): string {
  const r = batch.result;
  const lines = [
    `Document: ${batch.file}`,
    `Type: ${batch.type}`,
    `Borrower: ${borrowerOf(batch) || "Not identified"}`,
    `Loan number: ${batch.loan_match.loan_num || "Not identified"}`,
    ...flattenFields(r.extracted_data, "extracted_data").map(
      ([k, v]) => `${humanize(k.replace(/^extracted_data\./, ""))}: ${v}`,
    ),
    ...Object.entries(r.contacts).map(
      ([role, c]) =>
        `${roleLabel(role)}: ${[c.name, c.company, c.phone, c.email].filter(Boolean).join(", ")}`,
    ),
    ...(r.risks ? [`Notes: ${r.risks}`] : []),
    ...r.conditions.map(
      (c) => `Condition ${c.num}: ${c.desc} | ${c.party} | ${c.status}`,
    ),
  ];
  return "Processor Assistant - Scan results\n\n" + lines.join("\n");
}

function download(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function useCopy(): [boolean, (text: string) => Promise<void>] {
  const [copied, setCopied] = useState(false);
  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };
  return [copied, copy];
}

const actionButton =
  "inline-flex items-center gap-2 rounded-lg border border-transparent bg-subtle px-3 py-2 text-[13px] font-medium " +
  "text-foreground transition hover:bg-brand-soft hover:text-brand disabled:opacity-50";

// ---------- sections ----------
function SectionTitle({
  children,
  count,
}: {
  children: React.ReactNode;
  count?: number;
}) {
  return (
    <h3 className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.1em] text-muted">
      {children}
      {count !== undefined && (
        <span className="rounded bg-subtle px-1.5 py-px text-[10px] tracking-normal">
          {count}
        </span>
      )}
    </h3>
  );
}

export function ContactsGrid({
  contacts,
}: {
  contacts: Record<string, Contact>;
}) {
  const entries = Object.entries(contacts);
  if (!entries.length) return null;
  return (
    <section>
      <SectionTitle count={entries.length}>Contacts</SectionTitle>
      <div className="grid gap-2 sm:grid-cols-2">
        {entries.map(([role, c]) => (
          <div
            key={role}
            className="flex gap-3 rounded-xl bg-subtle/55 px-3.5 py-3"
          >
            <span className="grid size-8 shrink-0 place-items-center rounded-full bg-brand-soft text-brand">
              <UserRound className="size-4" />
            </span>
            <div className="min-w-0 text-[13px]">
              <p className="text-[11px] font-medium uppercase tracking-wide text-muted">
                {roleLabel(role)}
              </p>
              <p className="truncate font-medium text-foreground">{c.name}</p>
              {c.company && <p className="truncate text-muted">{c.company}</p>}
              <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted">
                {c.phone && (
                  <a
                    href={`tel:${c.phone}`}
                    className="inline-flex items-center gap-1 hover:text-brand"
                  >
                    <Phone className="size-3" />
                    {c.phone}
                  </a>
                )}
                {c.email && (
                  <a
                    href={`mailto:${c.email}`}
                    className="inline-flex min-w-0 items-center gap-1 truncate hover:text-brand"
                  >
                    <Mail className="size-3" />
                    {c.email}
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export function FieldsTable({ data }: { data: Record<string, unknown> }) {
  const [showAll, setShowAll] = useState(false);
  const rows = flattenFields(data);
  if (!rows.length) return null;
  const visible = showAll ? rows : rows.slice(0, 12);
  return (
    <section>
      <SectionTitle count={rows.length}>Extracted fields</SectionTitle>
      <dl className="divide-y divide-border/70 border-y border-border/70">
        {visible.map(([key, value]) => (
          <div
            key={key}
            className="grid grid-cols-[minmax(0,2fr)_minmax(0,3fr)] gap-3 px-2 py-2.5 text-[13px]"
          >
            <dt className="truncate text-muted" title={humanize(key)}>
              {humanize(key)}
            </dt>
            <dd className="break-words text-foreground">{value}</dd>
          </div>
        ))}
      </dl>
      {rows.length > 12 && (
        <button
          type="button"
          onClick={() => setShowAll(!showAll)}
          className="mt-2 text-xs font-medium text-brand hover:underline"
        >
          {showAll ? "Show fewer" : `Show all ${rows.length} fields`}
        </button>
      )}
    </section>
  );
}

export function OutputActions({ batch }: { batch: ScanBatch }) {
  const [busy, setBusy] = useState<"pdf" | "csv" | null>(null);
  const [error, setError] = useState("");
  const [copied, copy] = useCopy();

  const exportAs = async (kind: "pdf" | "csv") => {
    setBusy(kind);
    setError("");
    try {
      const blob =
        kind === "pdf" ? await exportPdf(batch) : await exportCsv(batch);
      download(blob, `loan-scan.${kind}`);
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : "The export did not finish. Try again.",
      );
    } finally {
      setBusy(null);
    }
  };

  return (
    <div>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className={actionButton}
          onClick={() => void copy(summaryText(batch))}
        >
          {copied ? (
            <Check className="size-4 text-emerald-600" />
          ) : (
            <ClipboardCopy className="size-4" />
          )}
          {copied ? "Copied" : "Copy results"}
        </button>
        <button
          type="button"
          className={actionButton}
          disabled={busy !== null}
          onClick={() => void exportAs("pdf")}
        >
          {busy === "pdf" ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <FileDown className="size-4" />
          )}{" "}
          Export PDF
        </button>
        <button
          type="button"
          className={actionButton}
          disabled={busy !== null}
          onClick={() => void exportAs("csv")}
        >
          {busy === "csv" ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <FileSpreadsheet className="size-4" />
          )}{" "}
          Export CSV
        </button>
      </div>
      {error && <p className="mt-2 text-xs text-rose-600">{error}</p>}
    </div>
  );
}

function gmailUrl(draft: EmailDraft, to = ""): string {
  const q = new URLSearchParams({
    view: "cm",
    fs: "1",
    to,
    su: draft.subject,
    body: draft.body,
  });
  return `https://mail.google.com/mail/?${q.toString()}`;
}

function DraftEditor({ title, draft }: { title: string; draft: EmailDraft }) {
  const [subject, setSubject] = useState(draft.subject);
  const [body, setBody] = useState(draft.body);
  const [copied, copy] = useCopy();
  return (
    <div className="rounded-xl bg-subtle/55 p-4">
      <p className="text-[13px] font-semibold text-foreground">{title}</p>
      <label className="mt-3 block text-[11px] font-medium uppercase tracking-wide text-muted">
        Subject
        <input
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 text-[13px] normal-case tracking-normal text-foreground focus:border-brand focus:outline-none"
        />
      </label>
      <label className="mt-3 block text-[11px] font-medium uppercase tracking-wide text-muted">
        Message
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={9}
          className="mt-1 w-full resize-y rounded-lg border border-border bg-card px-3 py-2 font-sans text-[13px] normal-case leading-relaxed tracking-normal text-foreground focus:border-brand focus:outline-none"
        />
      </label>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          className={actionButton}
          onClick={() => void copy(`Subject: ${subject}\n\n${body}`)}
        >
          {copied ? (
            <Check className="size-4 text-emerald-600" />
          ) : (
            <Copy className="size-4" />
          )}{" "}
          {copied ? "Copied" : "Copy email"}
        </button>
        <a
          className={actionButton}
          href={gmailUrl({ subject, body })}
          target="_blank"
          rel="noreferrer"
        >
          <Mailbox className="size-4" /> Open in Gmail
        </a>
      </div>
    </div>
  );
}

export function EmailDraftsPanel({ batch }: { batch: ScanBatch }) {
  const [drafts, setDrafts] = useState<EmailDrafts | null>(null);
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");

  const load = async () => {
    setState("loading");
    try {
      setDrafts(await emailDrafts(batch));
      setState("idle");
    } catch {
      setState("error");
    }
  };

  if (!drafts) {
    return (
      <section>
        <SectionTitle>Email drafts</SectionTitle>
        <button
          type="button"
          className={actionButton}
          disabled={state === "loading"}
          onClick={() => void load()}
        >
          {state === "loading" ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Mail className="size-4" />
          )}
          Draft borrower and loan officer emails
        </button>
        {state === "error" && (
          <p className="mt-2 text-xs text-rose-600">
            Could not build the drafts. Try again.
          </p>
        )}
      </section>
    );
  }
  return (
    <section>
      <SectionTitle>Email drafts</SectionTitle>
      <p className="mb-3 text-xs text-muted">
        Review the extracted details and drafts before sending. Nothing is sent
        from here.
      </p>
      <div className="grid gap-3 xl:grid-cols-2">
        <DraftEditor
          title="Borrower needs-list email"
          draft={drafts.borrower_needs_list}
        />
        <DraftEditor
          title="Loan officer status update"
          draft={drafts.loan_officer_update}
        />
      </div>
    </section>
  );
}

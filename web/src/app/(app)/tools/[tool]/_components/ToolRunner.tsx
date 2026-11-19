"use client";

import { useEffect, useState } from "react";
import { Loader2, Play } from "lucide-react";
import { ApiError, listLoans, runTool } from "@/lib/api";
import { TOOLS, type ToolBlock, type ToolField } from "@/lib/tools";
import type { LoanSummary } from "@/lib/types";
import ToolBlocks from "./ToolBlocks";

const inputClass =
  "mt-1.5 w-full rounded-xl border border-border bg-card px-3 py-2.5 text-sm text-foreground " +
  "shadow-card focus:border-brand focus:outline-none";

function Field({
  field,
  value,
  loans,
  onChange,
}: {
  field: ToolField;
  value: string;
  loans: LoanSummary[];
  onChange: (value: string) => void;
}) {
  const id = `tool-${field.name}`;
  let control: React.ReactNode;
  if (field.type === "textarea") {
    control = (
      <textarea
        id={id}
        rows={field.rows ?? 4}
        value={value}
        placeholder={field.placeholder}
        onChange={(event) => onChange(event.target.value)}
        className={inputClass + " resize-y"}
      />
    );
  } else if (field.type === "loan") {
    control = (
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)} className={inputClass}>
        <option value="">{loans.length ? "Choose a loan…" : "No loans yet"}</option>
        {loans.map((loan) => (
          <option key={loan.id} value={loan.id}>
            {loan.borrower || "Unnamed borrower"} ({loan.loan_num || "no number"})
          </option>
        ))}
      </select>
    );
  } else if (field.type === "select") {
    control = (
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)} className={inputClass}>
        {(field.options ?? []).map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
    );
  } else {
    control = (
      <input
        id={id}
        type={field.type === "number" ? "number" : field.type === "date" ? "date" : "text"}
        value={value}
        placeholder={field.placeholder}
        onChange={(event) => onChange(event.target.value)}
        className={inputClass}
      />
    );
  }
  return (
    <div>
      <label htmlFor={id} className="text-sm font-medium text-foreground">
        {field.label}
      </label>
      {control}
      {field.help && <p className="mt-1 text-xs text-muted">{field.help}</p>}
    </div>
  );
}

export default function ToolRunner({ toolKey }: { toolKey: string }) {
  const def = TOOLS[toolKey];
  const Icon = def.icon;
  // Dropdowns start on their first option, which is what the API assumes when a value is empty.
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      def.fields.filter((f) => f.type === "select" && f.options?.length).map((f) => [f.name, f.options![0]]),
    ),
  );
  const [loans, setLoans] = useState<LoanSummary[]>([]);
  const [running, setRunning] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [blocks, setBlocks] = useState<ToolBlock[]>([]);
  const needsLoans = def.fields.some((field) => field.type === "loan");

  useEffect(() => {
    if (!needsLoans) return;
    listLoans()
      .then((result) => setLoans(result.loans))
      .catch(() => setLoans([]));
  }, [needsLoans]);

  const missingRequired = !def.actions && def.fields.some((field) => field.required && !values[field.name]?.trim());

  const run = async (action?: string) => {
    setRunning(action ?? "run");
    setError("");
    try {
      const input: Record<string, unknown> = { ...values };
      if (action) input.action = action;
      const result = await runTool(def.key, input);
      setBlocks((result.output.blocks as ToolBlock[]) ?? []);
    } catch (e) {
      setBlocks([]);
      setError(e instanceof ApiError ? e.message : "That didn't finish. Try again.");
    } finally {
      setRunning(null);
    }
  };

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 md:px-8 md:py-10">
      <header className="flex items-start gap-4">
        <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-brand-soft text-brand">
          <Icon className="size-5" />
        </span>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">More tools</p>
          <h1 className="mt-1 text-[28px] font-semibold leading-tight tracking-tight text-foreground">
            {def.title}
          </h1>
          <p className="mt-1.5 text-sm text-muted">{def.description}</p>
        </div>
      </header>

      <section className="mt-8 space-y-5 rounded-2xl border border-border bg-card p-6 shadow-card">
        {def.fields.map((field) => (
          <Field
            key={field.name}
            field={field}
            value={values[field.name] ?? ""}
            loans={loans}
            onChange={(value) => setValues((current) => ({ ...current, [field.name]: value }))}
          />
        ))}
        <div className="flex flex-wrap gap-2 pt-1">
          {def.actions ? (
            def.actions.map((action) => (
              <button
                key={action.id}
                type="button"
                disabled={running !== null}
                onClick={() => void run(action.id)}
                className={
                  "inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition disabled:opacity-50 " +
                  (action.primary
                    ? "bg-brand text-white shadow-sm hover:bg-brand-strong"
                    : "border border-border bg-card text-foreground shadow-card hover:bg-subtle")
                }
              >
                {running === action.id && <Loader2 className="size-4 animate-spin" />}
                {action.label}
              </button>
            ))
          ) : (
            <button
              type="button"
              disabled={running !== null || missingRequired}
              onClick={() => void run()}
              className="inline-flex items-center gap-2 rounded-xl bg-brand px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-brand-strong disabled:opacity-50"
            >
              {running ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
              {def.runLabel ?? "Run"}
            </button>
          )}
        </div>
      </section>

      {error && (
        <p className="mt-5 rounded-xl border border-rose-500/25 bg-rose-500/[0.07] px-4 py-3 text-sm text-rose-700 dark:text-rose-300">
          {error}
        </p>
      )}
      {blocks.length > 0 && (
        <div className="mt-6">
          <ToolBlocks blocks={blocks} />
        </div>
      )}
    </div>
  );
}

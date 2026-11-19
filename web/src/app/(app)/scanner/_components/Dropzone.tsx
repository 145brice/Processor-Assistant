"use client";

import { useRef, useState } from "react";
import { Plus, UploadCloud } from "lucide-react";

const READS = ["Approval letters", "Purchase contracts", "1003s", "Bank statements", "Pay stubs", "W-2s"];

export default function Dropzone({ onFiles, compact = false }: { onFiles: (files: File[]) => void; compact?: boolean }) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  const take = (list: FileList | null) => {
    const files = Array.from(list ?? []);
    if (files.length) onFiles(files);
  };
  const open = () => input.current?.click();

  const shared = {
    role: "button" as const,
    tabIndex: 0,
    onClick: open,
    onKeyDown: (e: React.KeyboardEvent) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } },
    onDragOver: (e: React.DragEvent) => { e.preventDefault(); setOver(true); },
    onDragLeave: () => setOver(false),
    onDrop: (e: React.DragEvent) => { e.preventDefault(); setOver(false); take(e.dataTransfer.files); },
  };

  const fileInput = (
    <input ref={input} type="file" accept="application/pdf,.pdf" multiple hidden
      onChange={(e) => { take(e.target.files); e.target.value = ""; }} />
  );

  if (compact) {
    return (
      <div {...shared}
        className={"group flex cursor-pointer items-center gap-3 rounded-xl border border-dashed px-4 py-3 text-sm transition " +
          (over ? "border-brand bg-brand-soft" : "border-border bg-card hover:border-brand/50")}>
        <span className="grid size-7 place-items-center rounded-lg bg-brand-soft text-brand"><Plus className="size-4" /></span>
        <span className="font-medium text-foreground">Add more PDFs</span>
        <span className="text-muted">drop here or click</span>
        {fileInput}
      </div>
    );
  }

  return (
    <div {...shared}
      className={"group relative isolate cursor-pointer overflow-hidden rounded-2xl border bg-card shadow-card transition duration-200 " +
        (over ? "scale-[1.01] border-brand ring-4 ring-brand/15" : "border-border hover:border-brand/40 hover:shadow-md")}>
      <div className="bg-dots pointer-events-none absolute inset-0 -z-10 opacity-60 [mask-image:radial-gradient(ellipse_at_center,black,transparent_75%)]" />
      <div className="pointer-events-none absolute left-1/2 top-10 -z-10 size-40 -translate-x-1/2 rounded-full bg-brand/15 blur-3xl transition group-hover:bg-brand/25" />

      <div className="flex flex-col items-center px-6 pb-10 pt-12 text-center">
        <div className={"grid size-14 place-items-center rounded-2xl bg-gradient-to-b from-brand to-brand-strong text-white shadow-lg shadow-brand/25 ring-1 ring-white/20 transition duration-200 " +
          (over ? "-translate-y-1 scale-105" : "group-hover:-translate-y-0.5")}>
          <UploadCloud className="size-6" />
        </div>
        <p className="mt-5 text-[15px] font-semibold tracking-tight text-foreground">
          {over ? "Drop to add your files" : "Drop loan PDFs here"}
        </p>
        <p className="mt-1 text-sm text-muted">
          or <span className="font-medium text-brand underline-offset-4 group-hover:underline">browse your computer</span>. PDF only, up to 40 MB each.
        </p>
        <div className="mt-6 flex max-w-lg flex-wrap justify-center gap-1.5">
          {READS.map((r) => (
            <span key={r} className="rounded-md border border-border bg-surface/80 px-2 py-0.5 text-[11px] font-medium text-muted">{r}</span>
          ))}
          <span className="rounded-md px-1.5 py-0.5 text-[11px] font-medium text-muted">+ 13 more</span>
        </div>
      </div>
      {fileInput}
    </div>
  );
}

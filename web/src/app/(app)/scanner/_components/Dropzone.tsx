"use client";

import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";

export default function Dropzone({ onFiles, compact = false }: { onFiles: (files: File[]) => void; compact?: boolean }) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  const take = (list: FileList | null) => {
    const files = Array.from(list ?? []);
    if (files.length) onFiles(files);
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => input.current?.click()}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.current?.click(); } }}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); take(e.dataTransfer.files); }}
      className={
        "group flex cursor-pointer items-center rounded-2xl border-2 border-dashed text-center transition " +
        (compact ? "gap-4 px-5 py-4 text-left " : "flex-col justify-center px-6 py-14 ") +
        (over ? "border-brand bg-brand-soft" : "border-border bg-card hover:border-brand/50 hover:bg-subtle")
      }
    >
      <div className={"grid shrink-0 place-items-center rounded-xl bg-brand-soft text-brand transition group-hover:scale-105 " + (compact ? "size-10" : "size-14")}>
        <UploadCloud className={compact ? "size-5" : "size-7"} />
      </div>
      <div className={compact ? "" : "mt-4"}>
        <p className="font-medium text-foreground">
          {compact ? "Add more PDFs" : "Drop loan PDFs here"}
          <span className="font-normal text-muted"> or </span>
          <span className="text-brand underline-offset-2 group-hover:underline">browse files</span>
        </p>
        <p className="mt-1 text-xs text-muted">PDF only · up to 40 MB each · the type is detected automatically</p>
      </div>
      <input
        ref={input}
        type="file"
        accept="application/pdf,.pdf"
        multiple
        hidden
        onChange={(e) => { take(e.target.files); e.target.value = ""; }}
      />
    </div>
  );
}

import { Upload } from "lucide-react";

export default function ImportButton({
  onImport,
}: {
  onImport: (file: File) => void;
}) {
  return (
    <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-border bg-card px-4 py-2 text-sm font-medium text-foreground">
      <Upload className="size-4" /> Import
      <input
        type="file"
        accept=".csv,.json"
        className="sr-only"
        onChange={(event) =>
          event.target.files?.[0] && onImport(event.target.files[0])
        }
      />
    </label>
  );
}

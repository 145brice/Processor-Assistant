import { Archive } from "lucide-react";

export default function EmptyState({ removed = false }: { removed?: boolean }) {
  return (
    <div className="rounded-2xl border border-dashed border-border bg-card p-12 text-center shadow-card">
      <Archive className="mx-auto size-8 text-muted" />
      <h2 className="mt-4 font-semibold text-foreground">
        {removed ? "No removed loans" : "Your pipeline is empty"}
      </h2>
      <p className="mt-1 text-sm text-muted">
        {removed
          ? "Removed loans will appear here until they expire."
          : "Add a loan to start tracking documents and deadlines."}
      </p>
    </div>
  );
}

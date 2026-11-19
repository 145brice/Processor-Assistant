import { Search } from "lucide-react";
import type { LoanStatus } from "@/lib/types";
import { STATUSES } from "./LoanCard";

export default function FilterBar({
  status,
  query,
  mine,
  setStatus,
  setQuery,
  setMine,
  search,
}: {
  status: LoanStatus | "";
  query: string;
  mine: boolean;
  setStatus: (value: LoanStatus | "") => void;
  setQuery: (value: string) => void;
  setMine: (value: boolean) => void;
  search: () => void;
}) {
  return (
    <div className="mb-5 flex flex-wrap items-center gap-3">
      <div className="relative min-w-56 flex-1">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && search()}
          placeholder="Search loan or borrower"
          className="w-full rounded-xl border border-border bg-card py-2.5 pl-9 pr-3 text-sm text-foreground shadow-card"
        />
      </div>
      <select
        value={status}
        onChange={(event) => setStatus(event.target.value as LoanStatus | "")}
        className="rounded-xl border border-border bg-card px-3 py-2.5 text-sm text-foreground"
      >
        <option value="">All statuses</option>
        {STATUSES.map((value) => (
          <option key={value}>{value}</option>
        ))}
      </select>
      <label className="inline-flex items-center gap-2 text-sm text-muted">
        <input
          type="checkbox"
          checked={mine}
          onChange={(event) => setMine(event.target.checked)}
        />{" "}
        My loans
      </label>
    </div>
  );
}

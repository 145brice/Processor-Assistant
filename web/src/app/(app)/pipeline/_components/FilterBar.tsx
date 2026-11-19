import { Search } from "lucide-react";
import type { LoanSort, LoanStatus } from "@/lib/types";
import { STATUSES } from "./LoanCard";

const SORTS: { value: LoanSort; label: string }[] = [
  { value: "newest", label: "Newest" },
  { value: "borrower", label: "Borrower A-Z" },
  { value: "close", label: "Closing date" },
  { value: "lock", label: "Lock expiry" },
  { value: "loan_num", label: "Loan number" },
  { value: "status", label: "Status" },
];

export default function FilterBar({
  status,
  query,
  mine,
  sort,
  setStatus,
  setQuery,
  setMine,
  setSort,
  search,
}: {
  status: LoanStatus | "";
  query: string;
  mine: boolean;
  sort: LoanSort;
  setStatus: (value: LoanStatus | "") => void;
  setQuery: (value: string) => void;
  setMine: (value: boolean) => void;
  setSort: (value: LoanSort) => void;
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
      <select
        aria-label="Sort loans"
        value={sort}
        onChange={(event) => setSort(event.target.value as LoanSort)}
        className="rounded-xl border border-border bg-card px-3 py-2.5 text-sm text-foreground"
      >
        {SORTS.map((option) => (
          <option key={option.value} value={option.value}>
            Sort: {option.label}
          </option>
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

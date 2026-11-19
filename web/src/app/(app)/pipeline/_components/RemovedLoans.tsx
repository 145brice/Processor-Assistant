import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";
import { removedLoans, restoreLoan } from "@/lib/api";
import type { LoanSummary } from "@/lib/types";
import EmptyState from "./EmptyState";

export default function RemovedLoans() {
  const [open, setOpen] = useState(false);
  const [loans, setLoans] = useState<LoanSummary[]>([]);
  useEffect(() => {
    if (open)
      removedLoans()
        .then((result) => setLoans(result.loans))
        .catch(() => undefined);
  }, [open]);
  return (
    <section className="mt-10">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-sm font-semibold text-muted"
      >
        <ChevronDown
          className={`size-4 transition ${open ? "rotate-180" : ""}`}
        />{" "}
        Removed loans
      </button>
      {open && (
        <div className="mt-4">
          {loans.length ? (
            loans.map((loan) => (
              <div
                key={loan.id}
                className="flex items-center justify-between rounded-xl border border-border bg-card p-4 text-sm"
              >
                <span className="text-foreground">
                  {loan.borrower} · {loan.loan_num}
                </span>
                <button
                  type="button"
                  onClick={() =>
                    void restoreLoan(loan.id).then(() =>
                      setLoans(loans.filter((item) => item.id !== loan.id)),
                    )
                  }
                  className="text-brand"
                >
                  Restore
                </button>
              </div>
            ))
          ) : (
            <EmptyState removed />
          )}
        </div>
      )}
    </section>
  );
}

import { useState } from "react";

export default function AddLoanForm({
  onAdd,
}: {
  onAdd: (loanNum: string, borrower: string) => void;
}) {
  const [loanNum, setLoanNum] = useState("");
  const [borrower, setBorrower] = useState("");
  return (
    <section className="mb-6 rounded-2xl border border-border bg-card p-5 shadow-card">
      <div className="grid gap-3 sm:grid-cols-2">
        <input
          value={loanNum}
          onChange={(event) => setLoanNum(event.target.value)}
          placeholder="Loan number"
          className="rounded-xl border border-border bg-surface px-3 py-2 text-foreground"
        />
        <input
          value={borrower}
          onChange={(event) => setBorrower(event.target.value)}
          placeholder="Borrower name"
          className="rounded-xl border border-border bg-surface px-3 py-2 text-foreground"
        />
      </div>
      <button
        type="button"
        disabled={!loanNum.trim() || !borrower.trim()}
        onClick={() => {
          onAdd(loanNum, borrower);
          setLoanNum("");
          setBorrower("");
        }}
        className="mt-3 rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
      >
        Save loan
      </button>
    </section>
  );
}

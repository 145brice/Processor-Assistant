"use client";

import { useCallback, useEffect, useState } from "react";
import { FilePlus2 } from "lucide-react";
import {
  ApiError,
  createLoan,
  deleteLoan,
  importLoans,
  listLoans,
  setLoanStatus,
} from "@/lib/api";
import type { LoanStatus, LoanSummary, StatusCounts } from "@/lib/types";
import AddLoanForm from "./_components/AddLoanForm";
import EmptyState from "./_components/EmptyState";
import FilterBar from "./_components/FilterBar";
import ImportButton from "./_components/ImportButton";
import LoanCard, { STATUSES, STATUS_STYLE } from "./_components/LoanCard";
import PipelineHeader from "./_components/PipelineHeader";
import RemovedLoans from "./_components/RemovedLoans";

export default function Page() {
  const [loans, setLoans] = useState<LoanSummary[]>([]);
  const [counts, setCounts] = useState<StatusCounts | null>(null);
  const [status, setStatus] = useState<LoanStatus | "">("");
  const [query, setQuery] = useState("");
  const [mine, setMine] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [addOpen, setAddOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await listLoans({
        status: status || undefined,
        q: query || undefined,
        mine,
      });
      setLoans(result.loans);
      setCounts(result.counts);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not load the pipeline.",
      );
    } finally {
      setLoading(false);
    }
  }, [mine, query, status]);

  useEffect(() => {
    const value = new URLSearchParams(window.location.search).get("status");
    if (STATUSES.includes(value as LoanStatus)) setStatus(value as LoanStatus);
  }, []);
  useEffect(() => {
    void load();
  }, [load]);

  const addLoan = async (loanNum: string, borrower: string) => {
    try {
      await createLoan({ loan_num: loanNum, borrower, status: "Pending" });
      setAddOpen(false);
      await load();
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : "Could not add the loan.",
      );
    }
  };
  const importFile = async (file: File) => {
    try {
      await importLoans(file);
      await load();
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not import the pipeline.",
      );
    }
  };
  const changeStatus = async (id: number, next: LoanStatus) => {
    try {
      await setLoanStatus(id, next);
      await load();
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not update the loan.",
      );
    }
  };
  const remove = async (id: number) => {
    try {
      await deleteLoan(id);
      await load();
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not remove the loan.",
      );
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 md:px-8">
      <PipelineHeader />
      <div className="mb-6 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setAddOpen(!addOpen)}
          className="inline-flex items-center gap-2 rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-white"
        >
          <FilePlus2 className="size-4" /> Add loan
        </button>
        <ImportButton onImport={(file) => void importFile(file)} />
      </div>
      {addOpen && (
        <AddLoanForm
          onAdd={(loanNum, borrower) => void addLoan(loanNum, borrower)}
        />
      )}
      {error && (
        <p className="mb-5 rounded-xl border border-rose-500/25 bg-rose-500/[0.07] p-4 text-sm text-rose-600">
          {error}
        </p>
      )}
      <FilterBar
        status={status}
        query={query}
        mine={mine}
        setStatus={setStatus}
        setQuery={setQuery}
        setMine={setMine}
        search={() => void load()}
      />
      {counts && (
        <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-5">
          {STATUSES.map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setStatus(value)}
              className="rounded-xl border border-border bg-card p-3 text-left shadow-card"
            >
              <span
                className={`inline-flex items-center gap-1.5 text-xs ${STATUS_STYLE[value]}`}
              >
                <span className="size-1.5 rounded-full bg-current" />
                {value}
              </span>
              <strong className="mt-1 block text-lg text-foreground">
                {counts[value.toLowerCase() as keyof StatusCounts]}
              </strong>
            </button>
          ))}
        </div>
      )}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[1, 2, 3].map((value) => (
            <div
              key={value}
              className="skeleton h-48 animate-pulse rounded-2xl"
            />
          ))}
        </div>
      ) : loans.length ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {loans.map((loan) => (
            <LoanCard
              key={loan.id}
              loan={loan}
              onStatus={(id, next) => void changeStatus(id, next)}
              onDelete={(id) => void remove(id)}
            />
          ))}
        </div>
      ) : (
        <EmptyState />
      )}
      <RemovedLoans />
    </div>
  );
}

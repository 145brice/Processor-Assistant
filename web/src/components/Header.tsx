// Skeleton "MY PIPELINE" header. Task T-10 loads real counts from listLoans().counts and links
// each chip to /pipeline?status=<status>.
const CHIPS = ["All", "Pending UW", "Requested", "Cleared", "Overdue", "Closed"];

export default function Header() {
  return (
    <header className="flex items-center gap-2 border-b border-slate-300 bg-slate-100 px-4 py-3">
      <span className="mr-2 text-sm font-bold tracking-widest text-slate-700">MY PIPELINE</span>
      {CHIPS.map((chip) => (
        <span key={chip} className="rounded border border-slate-300 bg-white px-2 py-1 text-sm text-slate-700">
          – {chip}
        </span>
      ))}
    </header>
  );
}

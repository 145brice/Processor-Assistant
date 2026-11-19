import { Check } from "lucide-react";

const STEPS = ["Upload", "Review types", "Scan", "Results"];

/** `current` is the index of the active step; earlier steps show as done. */
export default function Steps({ current }: { current: number }) {
  return (
    <ol className="flex items-center gap-2 text-xs font-medium">
      {STEPS.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <li key={label} className="flex items-center gap-2">
            <span
              className={
                "grid size-5 place-items-center rounded-full text-[10px] font-semibold tabular-nums transition-colors " +
                (done ? "bg-brand text-white" : active ? "bg-brand-soft text-brand ring-1 ring-brand/40" : "bg-subtle text-muted")
              }
            >
              {done ? <Check className="size-3" strokeWidth={3} /> : i + 1}
            </span>
            <span className={"hidden sm:inline " + (active ? "text-foreground" : "text-muted")}>{label}</span>
            {i < STEPS.length - 1 && <span className={"h-px w-4 sm:w-8 " + (done ? "bg-brand/60" : "bg-border")} />}
          </li>
        );
      })}
    </ol>
  );
}

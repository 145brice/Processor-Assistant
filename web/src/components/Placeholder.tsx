import { Hammer } from "lucide-react";

// Shown by every page that is not built yet. Delete it from a page when its task is done.
// `task` and `notes` are for developers: they stay in the HTML (data attributes), not on screen.
export default function Placeholder({ title, task, notes }: { title: string; task: string; notes?: string }) {
  return (
    <section className="mx-auto w-full max-w-5xl px-4 py-8 md:px-8 md:py-10" data-task={task} data-notes={notes}>
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
      <div className="mt-6 flex flex-col items-center rounded-2xl border border-dashed border-border bg-card px-6 py-16 text-center shadow-card">
        <div className="grid size-12 place-items-center rounded-xl bg-brand-soft text-brand">
          <Hammer className="size-6" />
        </div>
        <p className="mt-4 text-base font-medium text-foreground">Coming soon</p>
        <p className="mt-1 max-w-md text-sm text-muted">
          We&apos;re moving {title} to the new Processor Assistant. It will appear here shortly.
        </p>
      </div>
    </section>
  );
}

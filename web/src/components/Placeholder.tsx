// Shown by every page that is not built yet. Delete it from a page when its task is done.
export default function Placeholder({ title, task, notes }: { title: string; task: string; notes?: string }) {
  return (
    <section className="p-8">
      <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
      <p className="mt-2 text-slate-600">
        Not built yet: see <strong>{task}</strong> in docs/nextjs-rebuild/TASKS.md.
      </p>
      {notes && <p className="mt-1 text-sm text-slate-500">{notes}</p>}
    </section>
  );
}

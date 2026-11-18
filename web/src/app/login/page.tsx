"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowRight, FileSearch, ListChecks, Loader2, ScanLine, ShieldCheck } from "lucide-react";
import { supabase } from "@/lib/supabase";
import { safeNext } from "@/lib/navigation";

const FEATURES = [
  { icon: FileSearch, title: "Scan loan documents", text: "Pull borrower and loan details straight out of your files." },
  { icon: ListChecks, title: "Track every condition", text: "See what is needed, requested and cleared across your pipeline." },
  { icon: ShieldCheck, title: "Private by design", text: "Documents are processed in memory and never stored." },
];

function GoogleLogo() {
  return (
    <svg viewBox="0 0 24 24" className="size-5" aria-hidden>
      <path fill="#4285F4" d="M23.5 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.45a5.5 5.5 0 0 1-2.4 3.62v3h3.88c2.27-2.09 3.57-5.17 3.57-8.81z" />
      <path fill="#34A853" d="M12 24c3.24 0 5.96-1.07 7.95-2.92l-3.88-3c-1.08.72-2.45 1.15-4.07 1.15-3.13 0-5.78-2.11-6.73-4.95H1.27v3.1A12 12 0 0 0 12 24z" />
      <path fill="#FBBC05" d="M5.27 14.28A7.2 7.2 0 0 1 4.9 12c0-.79.14-1.56.37-2.28v-3.1H1.27A12 12 0 0 0 0 12c0 1.94.46 3.77 1.27 5.38l4-3.1z" />
      <path fill="#EA4335" d="M12 4.77c1.76 0 3.34.61 4.59 1.8l3.44-3.44C17.95 1.19 15.24 0 12 0A12 12 0 0 0 1.27 6.62l4 3.1C6.22 6.88 8.87 4.77 12 4.77z" />
    </svg>
  );
}

export default function Page() {
  const router = useRouter();
  const [busy, setBusy] = useState<"google" | "sandbox" | null>(null);
  const signIn = async () => {
    setBusy("google");
    document.cookie = "pa_sandbox=; Path=/; Max-Age=0; SameSite=Lax";
    const next = safeNext(new URLSearchParams(window.location.search).get("next"), window.location.origin);
    const { error } = await supabase.auth.signInWithOAuth({ provider: "google", options: { redirectTo: window.location.origin + "/auth/callback?next=" + encodeURIComponent(next) } });
    if (error) setBusy(null);
  };
  const sandbox = async () => {
    setBusy("sandbox");
    await supabase.auth.signOut();
    document.cookie = "pa_sandbox=1; Path=/; SameSite=Lax";
    router.push("/scanner");
  };

  return (
    <main className="grid min-h-screen lg:grid-cols-[1.1fr_1fr]">
      <section className="relative hidden overflow-hidden bg-sidebar px-12 py-12 text-white lg:flex lg:flex-col">
        <div className="pointer-events-none absolute -right-32 -top-32 size-[28rem] rounded-full bg-brand/30 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-40 -left-20 size-[26rem] rounded-full bg-[#2f4c8f]/40 blur-3xl" />
        <div className="relative flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-xl bg-gradient-to-br from-brand to-[#2f4c8f] shadow-lg shadow-black/30">
            <ScanLine className="size-5" />
          </div>
          <span className="text-lg font-semibold tracking-tight">Processor Assistant</span>
        </div>
        <div className="relative my-auto max-w-lg py-12">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-sidebar-text/80">Online mortgage processing</p>
          <h1 className="mt-4 text-5xl font-semibold leading-[1.08] tracking-tight">Made for processors, built by processors.</h1>
          <ul className="mt-10 space-y-6">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <li key={title} className="flex gap-4">
                <div className="grid size-10 shrink-0 place-items-center rounded-lg bg-white/10 ring-1 ring-white/10">
                  <Icon className="size-5 text-white" />
                </div>
                <div>
                  <p className="font-medium">{title}</p>
                  <p className="mt-0.5 text-sm text-sidebar-text">{text}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-10 flex items-center gap-3 lg:hidden">
            <div className="grid size-10 place-items-center rounded-xl bg-gradient-to-br from-brand to-[#2f4c8f] text-white">
              <ScanLine className="size-5" />
            </div>
            <div>
              <p className="font-semibold tracking-tight">Processor Assistant</p>
              <p className="text-xs text-muted">Made for processors, built by processors.</p>
            </div>
          </div>

          <h2 className="text-2xl font-semibold tracking-tight">Welcome back</h2>
          <p className="mt-2 text-sm text-muted">Sign in to your workspace, or look around with a sample loan first.</p>

          <button
            type="button"
            onClick={() => void signIn()}
            disabled={busy !== null}
            className="mt-8 flex w-full items-center justify-center gap-3 rounded-xl border border-border bg-card px-4 py-3 text-sm font-medium shadow-card transition hover:bg-subtle disabled:opacity-60"
          >
            {busy === "google" ? <Loader2 className="size-5 animate-spin" /> : <GoogleLogo />}
            Continue with Google
          </button>

          <div className="my-6 flex items-center gap-3 text-xs text-muted">
            <span className="h-px flex-1 bg-border" />or<span className="h-px flex-1 bg-border" />
          </div>

          <button
            type="button"
            onClick={() => void sandbox()}
            disabled={busy !== null}
            className="group flex w-full items-center justify-center gap-2 rounded-xl bg-brand px-4 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-brand-strong disabled:opacity-60"
          >
            {busy === "sandbox" ? <Loader2 className="size-4 animate-spin" /> : null}
            Try with a sample loan
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
          </button>

          <p className="mt-8 text-center text-xs leading-relaxed text-muted">
            By continuing, you agree to the{" "}
            <Link className="font-medium text-brand hover:underline" href="/terms">Terms of Service</Link> and{" "}
            <Link className="font-medium text-brand hover:underline" href="/privacy">Privacy Policy</Link>.
          </p>
        </div>
      </section>
    </main>
  );
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { safeNext } from "@/lib/navigation";

export default function Page() {
  const router = useRouter();
  const signIn = async () => {
    document.cookie = "pa_sandbox=; Path=/; Max-Age=0; SameSite=Lax";
    const next = safeNext(new URLSearchParams(window.location.search).get("next"), window.location.origin);
    await supabase.auth.signInWithOAuth({ provider: "google", options: { redirectTo: window.location.origin + "/auth/callback?next=" + encodeURIComponent(next) } });
  };
  const sandbox = async () => {
    await supabase.auth.signOut();
    document.cookie = "pa_sandbox=1; Path=/; SameSite=Lax";
    router.push("/scanner");
  };
  return <main className="grid min-h-screen items-center gap-10 px-6 py-12 md:grid-cols-2 md:px-16">
    <section className="mx-auto max-w-xl">
      <p className="text-sm font-bold uppercase tracking-widest text-[#4368b8]">Processor Assistant</p>
      <h1 className="mt-4 text-4xl font-extrabold tracking-tight md:text-5xl">Process loan files with confidence.</h1>
      <p className="mt-5 text-lg text-[var(--muted)]">Scan documents, track conditions, and keep your mortgage pipeline moving from one secure workspace.</p>
    </section>
    <section className="mx-auto w-full max-w-md rounded-xl border border-[var(--border)] bg-[var(--card)] p-8 shadow-sm">
      <h2 className="text-2xl font-bold">Sign in to your workspace</h2>
      <p className="mt-2 text-sm text-[var(--muted)]">Use your Google account or explore with a sample loan.</p>
      <button type="button" onClick={() => void signIn()} className="mt-8 w-full rounded-lg bg-[#4368b8] px-4 py-3 font-semibold text-white hover:bg-[#36599e]">Continue with Google</button>
      <button type="button" onClick={sandbox} className="mt-3 w-full rounded-lg border border-[var(--border)] px-4 py-3 font-semibold">Try with a sample loan</button>
      <p className="mt-6 text-center text-xs text-[var(--muted)]">By continuing, you agree to the <Link className="text-blue-600" href="/terms">Terms</Link> and <Link className="text-blue-600" href="/privacy">Privacy Policy</Link>.</p>
    </section>
  </main>;
}

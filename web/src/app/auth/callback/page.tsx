"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function Page() {
  const router = useRouter();
  const [error, setError] = useState(false);
  useEffect(() => {
    const finish = async () => {
      const search = new URLSearchParams(window.location.search);
      const code = search.get("code");
      const result = code ? await supabase.auth.exchangeCodeForSession(code) : { error: new Error("Missing sign-in code") };
      if (result.error) { setError(true); return; }
      const next = search.get("next");
      const safeNext = next && next.startsWith("/") && !next.startsWith("//") && !next.startsWith("/\\") ? next : "/scanner";
      router.replace(safeNext);
    };
    void finish();
  }, [router]);
  return <main className="flex min-h-screen items-center justify-center"><div className="text-center"><p>{error ? "Sign-in failed, please try again." : "Signing you in…"}</p>{error && <a className="mt-3 inline-block text-blue-600" href="/login">Back to sign in</a>}</div></main>;
}

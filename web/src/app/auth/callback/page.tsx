"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { safeNext } from "@/lib/navigation";

export default function Page() {
  const router = useRouter();
  const [error, setError] = useState(false);
  useEffect(() => {
    const finish = async () => {
      const search = new URLSearchParams(window.location.search);
      const code = search.get("code");
      // The Supabase client may already have exchanged the code and removed it from the address, so a
      // session can exist even when the code is gone. Waiting on getSession lets that finish first.
      const result = code ? await supabase.auth.exchangeCodeForSession(code) : { error: new Error("Missing sign-in code") };
      if (result.error) {
        const { data } = await supabase.auth.getSession();
        if (!data.session) { setError(true); return; }
      }
      router.replace(safeNext(search.get("next"), window.location.origin));
    };
    void finish();
  }, [router]);
  return <main className="flex min-h-screen items-center justify-center"><div className="text-center"><p>{error ? "Sign-in failed, please try again." : "Signing you in…"}</p>{error && <a className="mt-3 inline-block text-blue-600" href="/login">Back to sign in</a>}</div></main>;
}

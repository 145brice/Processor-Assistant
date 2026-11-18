"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function Page() {
  const router = useRouter();
  useEffect(() => {
    const finish = async () => {
      const search = new URLSearchParams(window.location.search);
      const code = search.get("code");
      if (code) await supabase.auth.exchangeCodeForSession(code);
      router.replace(search.get("next") || "/scanner");
    };
    void finish();
  }, [router]);
  return <main className="flex min-h-screen items-center justify-center"><p>Signing you in…</p></main>;
}

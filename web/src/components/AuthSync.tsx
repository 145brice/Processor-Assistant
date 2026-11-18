"use client";

import { useEffect } from "react";
import { setAuth } from "@/lib/api";
import { supabase } from "@/lib/supabase";

export default function AuthSync() {
  useEffect(() => {
    let mounted = true;
    const sync = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (mounted) setAuth({ token: session?.access_token ?? null, sandbox: document.cookie.split("; ").includes("pa_sandbox=1") });
    };
    void sync();
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setAuth({ token: session?.access_token ?? null, sandbox: !session && document.cookie.split("; ").includes("pa_sandbox=1") });
    });
    return () => { mounted = false; subscription.unsubscribe(); };
  }, []);
  return null;
}

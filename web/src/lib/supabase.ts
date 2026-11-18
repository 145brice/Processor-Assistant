import { createBrowserClient } from "@supabase/ssr";

export const supabase = createBrowserClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL ?? "https://placeholder.invalid",
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "public-key-not-configured",
);

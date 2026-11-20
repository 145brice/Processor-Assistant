import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

const PUBLIC_PATHS = ["/login", "/auth/callback", "/privacy", "/terms"];

export async function middleware(request: NextRequest) {
  // Google sign-in can come back to the site's root (/?code=...), which is where the old app received
  // it, if Supabase's allowed list has the root address but not /auth/callback. Hand the code to the
  // callback page, which finishes the sign-in. Without this the code is dropped and sign-in loops.
  if (request.nextUrl.pathname === "/" && request.nextUrl.searchParams.has("code")) {
    const callback = request.nextUrl.clone();
    callback.pathname = "/auth/callback";
    return NextResponse.redirect(callback);
  }
  const response = NextResponse.next({ request });
  const sandbox = request.cookies.get("pa_sandbox")?.value === "1";
  const isPublic = PUBLIC_PATHS.some((path) => request.nextUrl.pathname === path);
  if (isPublic) return response;

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "",
    { cookies: { getAll: () => request.cookies.getAll(), setAll: (cookies) => cookies.forEach(({ name, value, options }) => response.cookies.set(name, value, options)) } },
  );
  const { data: { user } } = await supabase.auth.getUser();
  if (!user && !sandbox) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(login);
  }
  return response;
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };

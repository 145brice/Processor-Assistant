export function safeNext(value: string | null, origin: string): string {
  try {
    const url = new URL(value ?? "", origin);
    return url.origin === origin ? url.pathname + url.search : "/scanner";
  } catch {
    return "/scanner";
  }
}

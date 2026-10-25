/** A URL's host, or null for an empty or unparsable one (a client's `uri` is optional). */
export function hostOf(url: string): string | null {
  try {
    return new URL(url).host;
  } catch {
    return null;
  }
}

/** Where to go after login: a same-site path from `?next=`, else the dashboard. */
export function safeNextPath(next: string | null): string {
  // Resolve like the browser would (it strips tabs/newlines and treats \ as /), then keep it only if it stays on this origin
  const base = 'https://trava.invalid';
  if (!next || !next.startsWith('/')) return '/dashboard';
  const url = new URL(next, base);
  return url.origin === base ? url.pathname + url.search + url.hash : '/dashboard';
}

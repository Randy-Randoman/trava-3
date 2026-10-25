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
  if (!next || !next.startsWith('/') || next.startsWith('//') || next.startsWith('/\\')) {
    return '/dashboard';
  }
  return next;
}

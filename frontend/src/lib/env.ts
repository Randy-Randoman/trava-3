/**
 * Public env vars. Each `process.env.NEXT_PUBLIC_*` is referenced literally so
 * Next.js can inline it; values are checked lazily so a missing var only fails
 * where it is actually used.
 */
function required(name: string, value: string | undefined): string {
  if (!value) throw new Error(`Missing environment variable ${name}`)
  return value
}

export const env = {
  backendUrl: () => required('NEXT_PUBLIC_BACKEND_URL', process.env.NEXT_PUBLIC_BACKEND_URL),
  supabaseUrl: () => required('NEXT_PUBLIC_SUPABASE_URL', process.env.NEXT_PUBLIC_SUPABASE_URL),
  supabaseAnonKey: () => required('NEXT_PUBLIC_SUPABASE_ANON_KEY', process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY),
}

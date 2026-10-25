'use client'

/**
 * OAuth consent page (#54). Supabase Auth (the authorization server) sends the user here with
 * `?authorization_id=…` when an agent (Claude Code, claude.ai, …) asks to connect.
 * Not signed in → /login and back. A client the user already allowed gets a redirect instead
 * of details, and is sent straight on.
 */

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { OAuthAuthorizationDetails } from '@supabase/supabase-js'
import { useAuth } from '@/lib/auth'
import { supabase } from '@/lib/supabase/client'
import { hostOf } from '@/lib/oauth'

const FAILED = 'This sign-in request has expired or was already used. Start connecting again from your app.'

export default function ConsentPage() {
  const router = useRouter()
  const { user, loading } = useAuth()
  const [details, setDetails] = useState<OAuthAuthorizationDetails | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (loading) return
    if (!user) {
      router.replace(`/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`)
      return
    }
    const id = new URLSearchParams(window.location.search).get('authorization_id')
    if (!id) {
      setError(FAILED)
      return
    }
    supabase.auth.oauth.getAuthorizationDetails(id).then(({ data, error }) => {
      if (error || !data) setError(FAILED)
      else if ('redirect_url' in data) window.location.href = data.redirect_url
      else setDetails(data)
    })
  }, [user, loading, router])

  const decide = async (allow: boolean) => {
    if (!details) return
    setBusy(true)
    const oauth = supabase.auth.oauth
    const { data, error } = allow
      ? await oauth.approveAuthorization(details.authorization_id, { skipBrowserRedirect: true })
      : await oauth.denyAuthorization(details.authorization_id, { skipBrowserRedirect: true })
    if (error || !data) {
      setError(FAILED)
      setBusy(false)
    } else {
      window.location.href = data.redirect_url
    }
  }

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 px-4">
      <div className="mx-auto w-full max-w-md bg-white py-8 px-6 border-4 border-trava-black shadow-brutal">
        {error ? (
          <div className="bg-red-50 border-2 border-red-500 text-red-700 px-4 py-3 text-sm font-bold">{error}</div>
        ) : !details ? (
          <div className="text-gray-500 text-center">Loading...</div>
        ) : (
          <>
            <h1 className="text-2xl font-black uppercase tracking-tighter text-trava-black">
              Connect {details.client.name || 'an unnamed app'} to TRAVA?
            </h1>
            <p className="mt-2 text-sm text-gray-500">
              It will return to {hostOf(details.redirect_uri) ?? details.redirect_uri}
            </p>
            <p className="mt-6 text-sm font-bold text-trava-black uppercase tracking-wide">It will be able to</p>
            <p className="mt-1 text-trava-black">read and change your trips and boards, search hotels and the web.</p>
            <p className="mt-4 text-sm text-gray-600">You can disconnect it any time under Connected apps.</p>
            <div className="mt-6 flex gap-3">
              <button
                onClick={() => decide(false)}
                disabled={busy}
                className="flex-1 border-2 border-trava-black bg-white py-2 px-4 text-sm font-bold text-trava-black hover:bg-gray-100 transition-all disabled:opacity-50"
              >
                Deny
              </button>
              <button
                onClick={() => decide(true)}
                disabled={busy}
                className="flex-1 border-2 border-trava-black bg-adventure-orange py-2 px-4 text-sm font-bold text-trava-black hover:shadow-brutal hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all disabled:opacity-50"
              >
                Allow
              </button>
            </div>
            <p className="mt-4 text-center text-xs text-gray-500">Signed in as {details.user.email}</p>
          </>
        )}
      </div>
    </div>
  )
}

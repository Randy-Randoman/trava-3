'use client'

/**
 * Connected apps (#54): the OAuth clients (agents) the user has allowed, and disconnecting one.
 * Revoking a grant revokes the consent and the client's sessions; the backend's
 * require_agent rejects its next call.
 */

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import type { OAuthGrant } from '@supabase/supabase-js'
import { ProtectedRoute } from '@/components/auth'
import { supabase } from '@/lib/supabase/client'

function ConnectionsContent() {
  const [grants, setGrants] = useState<OAuthGrant[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    const { data, error } = await supabase.auth.oauth.listGrants()
    if (error) setError('Failed to load connected apps')
    else setGrants(data)
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const disconnect = async (grant: OAuthGrant) => {
    if (!confirm(`Disconnect ${grant.client.name || 'this app'}?`)) return
    const { error } = await supabase.auth.oauth.revokeGrant({ clientId: grant.client.id })
    if (error) setError('Failed to disconnect the app')
    else load()
  }

  return (
    <main className="max-w-2xl mx-auto px-4 py-8">
      <Link href="/dashboard" className="text-sm font-bold text-adventure-orange hover:underline">
        ← Back to trips
      </Link>
      <h1 className="mt-4 text-3xl font-black uppercase tracking-tighter text-trava-black">Connected apps</h1>
      <p className="mt-2 text-sm text-gray-600">Agents you allowed to read and change your trips and boards.</p>

      {error && (
        <div className="mt-6 bg-red-50 border-2 border-red-500 text-red-700 px-4 py-3 text-sm font-bold">{error}</div>
      )}

      {grants === null ? (
        !error && <div className="mt-6 text-gray-500">Loading...</div>
      ) : grants.length === 0 ? (
        <p className="mt-6 text-gray-500">No connected apps.</p>
      ) : (
        <ul className="mt-6 space-y-3">
          {grants.map((grant) => (
            <li
              key={grant.client.id}
              className="flex items-center justify-between bg-white border-2 border-trava-black px-4 py-3"
            >
              <div>
                <div className="font-bold text-trava-black">{grant.client.name || 'Unnamed app'}</div>
                <div className="text-xs text-gray-500">
                  Allowed {new Date(grant.granted_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                </div>
              </div>
              <button
                onClick={() => disconnect(grant)}
                className="px-3 py-1.5 border-2 border-trava-black text-sm font-bold text-red-600 hover:bg-red-50"
              >
                Disconnect
              </button>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}

export default function ConnectionsPage() {
  return (
    <ProtectedRoute>
      <ConnectionsContent />
    </ProtectedRoute>
  )
}

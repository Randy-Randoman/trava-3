'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { supabase } from '@/lib/supabase/client'

export default function PendingApprovalPage() {
  const router = useRouter()
  const { user, signOut, loading: authLoading } = useAuth()
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  const handleCheckAgain = async () => {
    setChecking(true)
    try {
      const { data } = await supabase
        .from('profiles')
        .select('is_approved')
        .eq('id', user?.id)
        .single()

      if (data?.is_approved) {
        router.push('/dashboard')
      }
    } finally {
      setChecking(false)
    }
  }

  const handleSignOut = async () => {
    await signOut()
    router.push('/login')
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center mb-6">
          <img
            src="/trava-logo.png"
            alt="Trava Logo"
            className="w-24 h-auto object-contain scale-x-[-1] drop-shadow-[4px_4px_0px_rgba(26,26,27,0.2)]"
          />
        </div>
        <h2 className="mt-2 text-center text-3xl font-black uppercase tracking-tighter text-trava-black">
          Account Under Review
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 border-4 border-trava-black shadow-brutal sm:px-10 text-center">
          <p className="text-trava-black font-medium mb-6">
            Your account is being reviewed. You'll be able to access Trava once an admin approves your account.
          </p>

          <div className="space-y-3">
            <button
              onClick={handleCheckAgain}
              disabled={checking}
              className="flex w-full justify-center border-2 border-trava-black bg-adventure-orange py-2 px-4 text-sm font-bold text-trava-black hover:shadow-brutal hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none disabled:translate-x-0 disabled:translate-y-0"
            >
              {checking ? 'Checking...' : 'Check again'}
            </button>

            <button
              onClick={handleSignOut}
              className="flex w-full justify-center border-2 border-trava-black bg-white py-2 px-4 text-sm font-bold text-trava-black hover:shadow-brutal hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all focus:outline-none"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

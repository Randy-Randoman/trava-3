'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { supabase } from '@/lib/supabase/client'

const AUTH_ENABLED = true

interface ProtectedRouteProps {
  children: React.ReactNode
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [approved, setApproved] = useState<boolean | null>(null)

  useEffect(() => {
    if (AUTH_ENABLED && !loading && !user) {
      router.push('/login')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (!AUTH_ENABLED || !user) return

    const checkApproval = async () => {
      const { data } = await supabase
        .from('profiles')
        .select('is_approved')
        .eq('id', user.id)
        .single()

      if (data?.is_approved === true) {
        setApproved(true)
      } else {
        router.push('/pending-approval')
      }
    }

    checkApproval()
  }, [user, router])

  if (!AUTH_ENABLED) {
    return <>{children}</>
  }

  if (loading || (user && approved === null)) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    )
  }

  if (!user || !approved) {
    return null
  }

  return <>{children}</>
}

'use client'

import { Suspense } from 'react'
import { useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { ChatInterface } from '@/components/chat'
import { BoardWrapper } from '@/components/canvas'
import BudgetPanel from '@/components/canvas/BudgetPanel'
import { useAuth } from '@/lib/auth'

function HomeContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [tripId, setTripId] = useState<string | undefined>()

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  // Redirect to the dashboard when no ?trip= param is given
  useEffect(() => {
    const tripParam = searchParams.get('trip')
    if (!tripParam && !authLoading) {
      router.push('/dashboard')
    }
  }, [searchParams, authLoading, router])

  // Load trip from URL query param on mount
  useEffect(() => {
    const tripParam = searchParams.get('trip')
    if (tripParam) {
      setTripId(tripParam)
    }
  }, [searchParams])

  // Navigate to dashboard
  const handleDashboard = () => {
    router.push('/dashboard')
  }

  // Show loading state while checking auth
  if (authLoading) {
    return (
      <div className="min-h-screen bg-retro-cream flex items-center justify-center">
        <div className="text-trava-black font-bold text-xl uppercase tracking-widest animate-pulse">Loading TRAVA...</div>
      </div>
    )
  }

  // Don't render if not authenticated
  if (!user) {
    return null
  }

  return (
    <main className="flex h-screen w-screen overflow-hidden bg-retro-cream">
      {/* Left Panel - Chat Interface (35%) */}
      <div className="w-[35%] border-r-4 border-trava-black bg-retro-cream h-full flex flex-col relative z-20">
        {tripId && (
          <ChatInterface
            tripId={tripId}
            onDashboard={handleDashboard}
          />
        )}
      </div>

      {/* Right Panel - Canvas/Board (65%) */}
      <div className="w-[65%] h-full relative bg-white">
        {tripId ? (
          <>
            <BoardWrapper tripId={tripId} />
            <BudgetPanel tripId={tripId} />
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-300 text-lg font-medium uppercase tracking-wider">
            Create a trip to start planning
          </div>
        )}
      </div>
    </main>
  )
}

export default function Home() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-retro-cream flex items-center justify-center">
        <div className="text-trava-black font-bold animate-pulse">Loading...</div>
      </div>
    }>
      <HomeContent />
    </Suspense>
  )
}

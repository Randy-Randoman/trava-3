'use client'

import { Suspense } from 'react'
import { useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { ChatInterface } from '@/components/chat'
import { BoardWrapper } from '@/components/canvas'
import BudgetPanel from '@/components/canvas/BudgetPanel'
import ShareButton from '@/components/canvas/ShareButton'
import { useAuth } from '@/lib/auth'
import { createTrip } from '@/lib/api'

// Set to true to enable authentication, false to bypass
const AUTH_ENABLED = true

function HomeContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [tripId, setTripId] = useState<string | undefined>()
  const [isCreatingTrip, setIsCreatingTrip] = useState(false)

  // Redirect to login if not authenticated (only if auth is enabled)
  useEffect(() => {
    if (AUTH_ENABLED && !authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  // Middleware handles redirect when no ?trip= param.
  // This is a fallback for edge cases (e.g. client-side navigation).
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

  // Create new trip via backend API
  const handleNewTrip = async () => {
    try {
      setIsCreatingTrip(true)
      console.log('🆕 Creating new trip...')

      const data = await createTrip({
        title: 'New Trip',
        destination: null
      })

      console.log('✅ Trip created:', data.id)
      setTripId(data.id)

      // Update URL
      router.push(`/?trip=${data.id}`)
    } catch (error) {
      console.error('Failed to create trip:', error)
      alert('Failed to create trip. Please try again.')
    } finally {
      setIsCreatingTrip(false)
    }
  }

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

  // Don't render if not authenticated (only if auth is enabled)
  if (AUTH_ENABLED && !user) {
    return null
  }

  return (
    <main className="flex h-screen w-screen overflow-hidden bg-retro-cream">
      {/* Left Panel - Chat Interface (35%) */}
      <div className="w-[35%] border-r-4 border-trava-black bg-retro-cream h-full flex flex-col relative z-20">
        {!tripId ? (
          // No trip selected - show welcome screen with New Trip button
          <div className="flex flex-col items-center justify-center h-full p-8 text-center bg-white/50">
            <div className="mb-8 rotate-3 group hover:rotate-6 transition-transform">
              <img src="/trava-logo.png" alt="Trava Logo" className="w-32 h-auto object-contain  drop-shadow-[5px_5px_0px_rgba(26,26,27,0.2)]" />
            </div>
            <h1 className="text-4xl font-black text-trava-black mb-4 uppercase tracking-tighter">Welcome to TRAVA</h1>
            <p className="text-gray-600 mb-10 max-w-md font-medium text-lg">
              Your AI-powered travel planning assistant. Create a new trip to get started!
            </p>
            <button
              onClick={handleNewTrip}
              disabled={isCreatingTrip}
              className="px-8 py-4 bg-adventure-orange border-2 border-trava-black text-trava-black text-xl font-bold uppercase tracking-wider brutal-shadow hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-none transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none disabled:translate-x-0 disabled:translate-y-0"
            >
              {isCreatingTrip ? 'Creating...' : '🚀 Start New Trip'}
            </button>
          </div>
        ) : (
          // Trip selected - show chat interface
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
            <ShareButton tripId={tripId} />
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

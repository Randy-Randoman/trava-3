'use client'

/**
 * Dashboard Page (Wave 4 - Issue #15)
 *
 * User's home view showing all their trips as cards.
 * Features: View, Rename, Delete trips
 */

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { getTrips, deleteTrip, updateTrip, createTrip, TripListItem } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { ProtectedRoute } from '@/components/auth'

function DashboardContent() {
  const router = useRouter()
  const { signOut } = useAuth()
  const [trips, setTrips] = useState<TripListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newTripOpen, setNewTripOpen] = useState(false)
  const [creatingTrip, setCreatingTrip] = useState(false)
  const [renameTarget, setRenameTarget] = useState<{ id: string; title: string } | null>(null)

  // Fetch trips on mount
  const fetchTrips = useCallback(async () => {
    try {
      setLoading(true)
      const data = await getTrips()
      setTrips(data.trips)
      setError(null)
    } catch (err) {
      setError('Failed to load trips')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTrips()
  }, [fetchTrips])

  // Handle delete
  const handleDelete = async (tripId: string, title: string) => {
    if (!confirm(`Delete "${title}"? This cannot be undone.`)) return

    try {
      await deleteTrip(tripId)
      setTrips(trips.filter(t => t.id !== tripId))
    } catch (err) {
      alert('Failed to delete trip')
      console.error(err)
    }
  }

  // Handle rename
  const handleRename = async (newTitle: string) => {
    if (!renameTarget || !newTitle || newTitle === renameTarget.title) {
      setRenameTarget(null)
      return
    }

    try {
      await updateTrip(renameTarget.id, { title: newTitle })
      setTrips(trips.map(t => t.id === renameTarget.id ? { ...t, title: newTitle } : t))
    } catch (err) {
      alert('Failed to rename trip')
      console.error(err)
    } finally {
      setRenameTarget(null)
    }
  }

  // Open trip in editor
  const handleOpen = (tripId: string) => {
    router.push(`/?trip=${tripId}`)
  }

  // Create new trip
  const handleNewTrip = () => {
    setNewTripOpen(true)
  }

  const handleCreateTrip = async (title: string) => {
    try {
      setCreatingTrip(true)
      const data = await createTrip({
        title,
        destination: null
      })
      setNewTripOpen(false)
      router.push(`/?trip=${data.id}`)
    } catch (err) {
      alert('Failed to create trip')
      console.error(err)
    } finally {
      setCreatingTrip(false)
    }
  }

  // Format date for display
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Unknown'
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading your trips...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-retro-cream border-b-4 border-trava-black sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img src="/trava-logo.png" alt="Trava Logo" className="h-10 w-auto object-contain " />
              <div>
                <h1 className="text-3xl font-black tracking-tighter text-trava-black uppercase leading-none">TRAVA</h1>
                <p className="text-xs text-gray-500 font-bold">Plan Smarter.</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleNewTrip}
                className="px-4 py-2 bg-white border-2 border-trava-black text-trava-black font-bold transition-all hover:bg-adventure-orange hover:shadow-brutal hover:translate-x-[-2px] hover:translate-y-[-2px] flex items-center gap-2 rounded-none"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                  <path d="M10.75 4.75a.75.75 0 0 0-1.5 0v4.5h-4.5a.75.75 0 0 0 0 1.5h4.5v4.5a.75.75 0 0 0 1.5 0v-4.5h4.5a.75.75 0 0 0 0-1.5h-4.5v-4.5Z" />
                </svg>
                New Trip
              </button>
              <button
                onClick={() => signOut()}
                className="px-4 py-2 bg-white border-2 border-trava-black text-trava-black font-bold transition-all hover:bg-adventure-orange hover:shadow-brutal hover:translate-x-[-2px] hover:translate-y-[-2px]"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 text-red-600 rounded-lg">
            {error}
          </div>
        )}

        {trips.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8 text-gray-400">
                <path fillRule="evenodd" d="M8.161 2.58a1.875 1.875 0 0 1 1.678 0l4.993 2.498c.106.052.23.052.336 0l3.869-1.935A1.875 1.875 0 0 1 21.75 4.82v12.485c0 .71-.401 1.36-1.037 1.677l-4.875 2.437a1.875 1.875 0 0 1-1.676 0l-4.994-2.497a.375.375 0 0 0-.336 0l-3.868 1.935A1.875 1.875 0 0 1 2.25 19.18V6.695c0-.71.401-1.36 1.036-1.677l4.875-2.438Z" clipRule="evenodd" />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-gray-800 mb-2">No trips yet</h2>
            <p className="text-gray-500 mb-6">Start planning your first adventure!</p>
            <button
              onClick={handleNewTrip}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Plan a Trip
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {trips.map((trip) => (
              <TripCard
                key={trip.id}
                trip={trip}
                onOpen={() => handleOpen(trip.id)}
                onRename={() => setRenameTarget({ id: trip.id, title: trip.title })}
                onDelete={() => handleDelete(trip.id, trip.title)}
                formatDate={formatDate}
              />
            ))}
          </div>
        )}
      </main>

      {/* New Trip Modal */}
      {newTripOpen && (
        <NewTripModal
          onClose={() => setNewTripOpen(false)}
          onCreate={handleCreateTrip}
          creating={creatingTrip}
        />
      )}

      {/* Rename Trip Modal */}
      {renameTarget && (
        <RenameModal
          currentTitle={renameTarget.title}
          onClose={() => setRenameTarget(null)}
          onRename={handleRename}
        />
      )}
    </div>
  )
}

// Trip Card Component
interface TripCardProps {
  trip: TripListItem
  onOpen: () => void
  onRename: () => void
  onDelete: () => void
  formatDate: (date: string | null) => string
}

function TripCard({ trip, onOpen, onRename, onDelete, formatDate }: TripCardProps) {
  const [menuOpen, setMenuOpen] = useState(false)

  // Build the image URL - use proxy for external URLs
  const getImageSrc = (url: string | null) => {
    if (!url) return null
    if (url.startsWith('data:')) return url // Base64 image
    // Use proxy for external URLs to avoid CORS
    return `/api/image-proxy?url=${encodeURIComponent(url)}`
  }

  const imageSrc = getImageSrc(trip.thumbnail_url)

  return (
    <div className={`bg-white border-4 border-trava-black brutal-shadow hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[6px_6px_0px_#1A1A1B] transition-all relative group ${menuOpen ? 'z-30' : ''}`}>
      {/* Thumbnail/Preview */}
      <div
        className="h-32 bg-trava-teal border-b-4 border-trava-black flex items-center justify-center cursor-pointer overflow-hidden p-2"
        onClick={onOpen}
      >
        {imageSrc ? (
          <img
            src={imageSrc}
            alt={trip.title}
            className="w-full h-full object-cover border-2 border-trava-black"
            onError={(e) => {
              // Fallback to icon on error
              e.currentTarget.style.display = 'none'
              e.currentTarget.nextElementSibling?.classList.remove('hidden')
            }}
          />
        ) : null}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className={`w-12 h-12 text-trava-black opacity-20 group-hover:scale-110 transition-transform ${imageSrc ? 'hidden' : ''}`}
        >
          <path fillRule="evenodd" d="M8.161 2.58a1.875 1.875 0 0 1 1.678 0l4.993 2.498c.106.052.23.052.336 0l3.869-1.935A1.875 1.875 0 0 1 21.75 4.82v12.485c0 .71-.401 1.36-1.037 1.677l-4.875 2.437a1.875 1.875 0 0 1-1.676 0l-4.994-2.497a.375.375 0 0 0-.336 0l-3.868 1.935A1.875 1.875 0 0 1 2.25 19.18V6.695c0-.71.401-1.36 1.036-1.677l4.875-2.438Z" clipRule="evenodd" />
        </svg>
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h3
              className="font-bold text-xl text-trava-black truncate cursor-pointer hover:text-adventure-orange"
              onClick={onOpen}
            >
              {trip.title}
            </h3>
            {trip.destination && (
              <p className="text-sm text-gray-500 truncate">{trip.destination}</p>
            )}
          </div>

          {/* Menu Button */}
          <div className="relative ml-2">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="p-1 text-gray-400 hover:text-gray-600 rounded"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                <path d="M10 3a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM10 8.5a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM11.5 15.5a1.5 1.5 0 1 0-3 0 1.5 1.5 0 0 0 3 0Z" />
              </svg>
            </button>

            {/* Dropdown Menu */}
            {menuOpen && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setMenuOpen(false)}
                />
                <div className="absolute right-0 mt-1 w-36 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20">
                  <button
                    onClick={() => { setMenuOpen(false); onOpen(); }}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                  >
                    Open
                  </button>
                  <button
                    onClick={() => { setMenuOpen(false); onRename(); }}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                  >
                    Rename
                  </button>
                  <button
                    onClick={() => { setMenuOpen(false); onDelete(); }}
                    className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50"
                  >
                    Delete
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-400">
          <span>Last edited {formatDate(trip.updated_at || trip.created_at)}</span>
          <span className={`px-2 py-0.5 rounded-full ${trip.status === 'active' ? 'bg-green-100 text-green-700' :
            trip.status === 'archived' ? 'bg-gray-100 text-gray-600' :
              'bg-yellow-100 text-yellow-700'
            }`}>
            {trip.status}
          </span>
        </div>
      </div>
    </div>
  )
}

// Rename Trip Modal Component
interface RenameModalProps {
  currentTitle: string
  onClose: () => void
  onRename: (newTitle: string) => void
}

function RenameModal({ currentTitle, onClose, onRename }: RenameModalProps) {
  const [title, setTitle] = useState(currentTitle)

  const handleSubmit = () => {
    const trimmed = title.trim()
    if (!trimmed) return
    onRename(trimmed)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-retro-cream border-4 border-trava-black shadow-[8px_8px_0px_#1A1A1B] w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b-4 border-trava-black">
          <h2 className="text-xl font-black uppercase tracking-tight text-trava-black">Rename Trip</h2>
          <button
            onClick={onClose}
            className="p-1 text-trava-black hover:text-adventure-orange transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-6 h-6">
              <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-5">
          <label className="block text-sm font-bold text-trava-black uppercase tracking-wide mb-2">
            Trip Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit() }}
            autoFocus
            maxLength={100}
            className="w-full bg-white border-2 border-trava-black px-4 py-3 text-sm font-medium text-trava-black placeholder:text-gray-400 focus:outline-none focus:shadow-brutal transition-all"
          />
          <div className="flex items-center justify-end gap-3 mt-4">
            <button
              onClick={onClose}
              className="px-5 py-2.5 border-2 border-trava-black text-trava-black font-black text-sm uppercase tracking-wide
                transition-all hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!title.trim() || title.trim() === currentTitle}
              className="px-6 py-2.5 bg-adventure-orange border-2 border-trava-black text-trava-black font-black text-sm uppercase tracking-wide
                transition-all hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[4px_4px_0px_#1A1A1B]
                active:translate-x-[1px] active:translate-y-[1px] active:shadow-none
                disabled:bg-gray-300 disabled:cursor-not-allowed disabled:border-gray-400 disabled:shadow-none"
            >
              Rename
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// New Trip Modal Component
interface NewTripModalProps {
  onClose: () => void
  onCreate: (title: string) => void
  creating: boolean
}

function NewTripModal({ onClose, onCreate, creating }: NewTripModalProps) {
  const [title, setTitle] = useState('')

  const handleSubmit = () => {
    const trimmed = title.trim()
    if (!trimmed) return
    onCreate(trimmed)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-retro-cream border-4 border-trava-black shadow-[8px_8px_0px_#1A1A1B] w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b-4 border-trava-black">
          <h2 className="text-xl font-black uppercase tracking-tight text-trava-black">New Trip</h2>
          <button
            onClick={onClose}
            className="p-1 text-trava-black hover:text-adventure-orange transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-6 h-6">
              <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-5">
          <label className="block text-sm font-bold text-trava-black uppercase tracking-wide mb-2">
            Trip Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit() }}
            placeholder="e.g. Summer in Italy"
            autoFocus
            maxLength={100}
            className="w-full bg-white border-2 border-trava-black px-4 py-3 text-sm font-medium text-trava-black placeholder:text-gray-400 focus:outline-none focus:shadow-brutal transition-all"
          />
          <div className="flex items-center justify-end mt-4">
            <button
              onClick={handleSubmit}
              disabled={creating || !title.trim()}
              className="px-6 py-2.5 bg-adventure-orange border-2 border-trava-black text-trava-black font-black text-sm uppercase tracking-wide
                transition-all hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[4px_4px_0px_#1A1A1B]
                active:translate-x-[1px] active:translate-y-[1px] active:shadow-none
                disabled:bg-gray-300 disabled:cursor-not-allowed disabled:border-gray-400 disabled:shadow-none"
            >
              {creating ? 'Creating...' : 'Create Trip'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Wrap with ProtectedRoute
export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  )
}

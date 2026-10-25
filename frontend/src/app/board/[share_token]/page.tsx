'use client'

/**
 * Public Board Page
 *
 * Read-only view of a shared trip board — no authentication required.
 * Accessible at /board/:share_token
 */

import dynamic from 'next/dynamic'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useCallback, useEffect, useRef, useState } from 'react'
import { getPublicBoard } from '@/lib/api'
import { useExcalidrawHydration } from '@/lib/hooks'
import '@excalidraw/excalidraw/index.css'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ExcalidrawAPI = any

const Excalidraw = dynamic(
  async () => (await import('@excalidraw/excalidraw')).Excalidraw,
  { ssr: false }
)

export default function PublicBoardPage() {
  const params = useParams()
  const shareToken = params.share_token as string

  const [title, setTitle] = useState<string>('')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [initialData, setInitialData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const originalFilesRef = useRef<Record<string, unknown>>({})
  const { setExcalidrawApi, hydrateImages, setOriginalFiles } = useExcalidrawHydration()

  const onExcalidrawApiReady = useCallback((api: ExcalidrawAPI) => {
    setExcalidrawApi(api)
    setOriginalFiles(originalFilesRef.current)
    setTimeout(() => hydrateImages(), 100)
  }, [setExcalidrawApi, hydrateImages, setOriginalFiles])

  useEffect(() => {
    if (!shareToken) return
    setLoading(true)
    getPublicBoard(shareToken)
      .then(data => {
        setTitle(data.title)
        originalFilesRef.current = data.files || {}
        setInitialData({
          elements: data.elements || [],
          appState: {
            viewBackgroundColor: '#FDFBF7',
          },
          scrollToContent: true,
          files: {},
        })
      })
      .catch(() => setError('This board could not be found or the link has expired.'))
      .finally(() => setLoading(false))
  }, [shareToken])

  if (loading) {
    return (
      <div className="min-h-screen bg-retro-cream flex items-center justify-center">
        <div className="text-trava-black font-bold text-xl uppercase tracking-widest animate-pulse">
          Loading board…
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-retro-cream flex flex-col items-center justify-center gap-4">
        <p className="text-trava-black font-bold text-lg">{error}</p>
        <Link href="/" className="text-sm underline text-gray-500 hover:text-trava-black">
          Go to Trava
        </Link>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-retro-cream relative z-10">
      {/* Minimal header */}
      <header className="bg-retro-cream border-b-4 border-trava-black px-6 py-3 flex items-center gap-3 shrink-0">
        <img src="/trava-logo.png" alt="Trava" className="h-8 w-auto object-contain" />
        <span className="font-black text-xl uppercase tracking-tighter text-trava-black">
          {title || 'Trip Board'}
        </span>
        <span className="ml-auto text-xs font-bold text-gray-400 uppercase tracking-wide border border-gray-300 px-2 py-0.5">
          Read only
        </span>
      </header>

      {/* Full-height canvas */}
      <div className="flex-1">
        {initialData && (
          <Excalidraw
            key={shareToken}
            initialData={initialData}
            viewModeEnabled={true}
            gridModeEnabled={false}
            excalidrawAPI={onExcalidrawApiReady}
          />
        )}
      </div>
    </div>
  )
}

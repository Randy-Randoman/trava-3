'use client'

/**
 * BoardWrapper - Excalidraw Canvas Component (Issue #10)
 *
 * Features:
 * - Load canvas state from backend GET /trips/{id}/canvas
 * - Auto-save with 2s debounce on change
 * - Hydrates images from URLs via proxy (Issue #13)
 */

import dynamic from 'next/dynamic'
import { useCallback, useEffect, useRef, useState } from 'react'
import { getCanvasState, saveCanvasState } from '@/lib/api'
import { useExcalidrawHydration } from '@/lib/hooks'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ExcalidrawAPI = any;

const Excalidraw = dynamic(
  async () => (await import('@excalidraw/excalidraw')).Excalidraw,
  { ssr: false }
)

interface BoardWrapperProps {
  tripId?: string
  readOnly?: boolean
}

const SAVE_DEBOUNCE_MS = 2000

export default function BoardWrapper({ tripId, readOnly = false }: BoardWrapperProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [initialData, setInitialData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  // Store the original files from backend (with URLs) for hydration
  const originalFilesRef = useRef<Record<string, unknown>>({})
  // Keep a ref to the Excalidraw API so we can read scene state on flush
  const excalidrawApiRef = useRef<ExcalidrawAPI | null>(null)

  // Hydration hook for loading URL-based images
  const { setExcalidrawApi, hydrateImages, clearCache, setOriginalFiles } = useExcalidrawHydration()

  // Callback when Excalidraw API is ready
  const onExcalidrawApiReady = useCallback((api: ExcalidrawAPI) => {
    excalidrawApiRef.current = api
    setExcalidrawApi(api)
    // Pass the original files from backend and hydrate
    setOriginalFiles(originalFilesRef.current)
    setTimeout(() => hydrateImages(), 100)
  }, [setExcalidrawApi, hydrateImages, setOriginalFiles])

  const loadCanvas = useCallback(async (shouldClearCache = false) => {
    setLoading(true)

    if (shouldClearCache) {
      clearCache()
    }

    if (!tripId) {
      setInitialData({ elements: [], files: {} })
      originalFilesRef.current = {}
      setLoading(false)
      return
    }

    try {
      const data = await getCanvasState(tripId)
      // Store the original files with URLs for hydration
      originalFilesRef.current = data.files || {}
      console.log('[BoardWrapper] Loaded files from backend:', Object.keys(originalFilesRef.current).length)

      setInitialData({
        elements: data.elements || [],
        appState: {
          ...data.appState,
          currentItemFontFamily: 2, // Default to "Normal" (Inter)
          viewBackgroundColor: '#FDFBF7', // Retro Cream
        },
        scrollToContent: true,
        // Pass empty files initially - we'll hydrate them after
        files: {},
      })
    } catch (err) {
      console.error('Failed to load canvas:', err)
      setInitialData({ elements: [], files: {} })
      originalFilesRef.current = {}
    } finally {
      setLoading(false)
    }
  }, [tripId, clearCache])

  // Load canvas from backend - reset loading when tripId changes
  useEffect(() => {
    loadCanvas(true)
  }, [loadCanvas])

  // Allow external triggers (e.g., chat transform) to force a reload without changing tripId
  useEffect(() => {
    const handleCanvasUpdated = (event: Event) => {
      const customEvent = event as CustomEvent<{ tripId?: string }>
      if (!tripId) return
      if (!customEvent.detail?.tripId || customEvent.detail.tripId === tripId) {
        loadCanvas(true)
      }
    }

    window.addEventListener('canvas-updated', handleCanvasUpdated)
    return () => {
      window.removeEventListener('canvas-updated', handleCanvasUpdated)
    }
  }, [tripId, loadCanvas])

  // Listen for flush-canvas events (fired by ShareButton before generating share link)
  // to ensure the latest canvas state is persisted before anyone opens the share URL.
  useEffect(() => {
    const handleFlush = async () => {
      const api = excalidrawApiRef.current
      if (!api || !tripId || readOnly) return

      // Cancel any pending debounced save
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
        saveTimeoutRef.current = null
      }

      try {
        const elements = api.getSceneElements()
        const files = api.getFiles()
        const originalFiles = originalFilesRef.current
        const filesToSave: Record<string, unknown> = {}
        for (const [id, file] of Object.entries(originalFiles)) {
          filesToSave[id] = file
        }
        if (files) {
          for (const [id, file] of Object.entries(files)) {
            if (!originalFiles[id]) {
              filesToSave[id] = file
            }
          }
        }

        await saveCanvasState(tripId, [...elements], filesToSave)
        console.log('[BoardWrapper] Canvas flushed for share')
      } catch (err) {
        console.error('[BoardWrapper] Failed to flush canvas:', err)
      }

      window.dispatchEvent(new CustomEvent('canvas-flushed'))
    }

    window.addEventListener('flush-canvas', handleFlush)
    return () => window.removeEventListener('flush-canvas', handleFlush)
  }, [tripId, readOnly])

  // Auto-save with debounce
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleChange = useCallback((elements: readonly any[], _appState: any, files: any) => {
    if (readOnly || !tripId || loading) return

    // Guard: Don't save if elements haven't changed from initial state
    if (elements.length === 0 && initialData?.elements?.length === 0) {
      return
    }

    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }

    saveTimeoutRef.current = setTimeout(async () => {
      try {
        // IMPORTANT: Preserve original files with URLs, not the hydrated base64 data
        // Merge: keep original URL-based files, but add any new user-added files
        const originalFiles = originalFilesRef.current
        const filesToSave: Record<string, unknown> = {}

        // First, copy all original files (these have the URLs we want to keep)
        for (const [id, file] of Object.entries(originalFiles)) {
          filesToSave[id] = file
        }

        // Then, add any NEW files that weren't in the original set
        // (these would be files the user added manually)
        if (files) {
          for (const [id, file] of Object.entries(files)) {
            if (!originalFiles[id]) {
              filesToSave[id] = file
            }
          }
        }

        await saveCanvasState(tripId, [...elements], filesToSave)
        console.log('🎨 Canvas saved (preserved URL-based files)')
        // Notify other components (e.g. BudgetPanel) that the canvas changed
        window.dispatchEvent(new CustomEvent('canvas-saved', { detail: { tripId } }))
      } catch (err) {
        console.error('Failed to save:', err)
      }
    }, SAVE_DEBOUNCE_MS)
  }, [tripId, readOnly, loading, initialData])

  // Cleanup
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current)
    }
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <span className="text-gray-400">Loading canvas...</span>
      </div>
    )
  }

  return (
    <div className="w-full h-full">
      <Excalidraw
        key={tripId || 'empty'}
        initialData={initialData}
        onChange={handleChange}
        viewModeEnabled={readOnly}
        gridModeEnabled={false}
        excalidrawAPI={onExcalidrawApiReady}
        UIOptions={{
          canvasActions: {
            export: { saveFileToDisk: true },
            loadScene: true,
            clearCanvas: true,
            changeViewBackgroundColor: true,
          },
        }}
      />
    </div>
  )
}

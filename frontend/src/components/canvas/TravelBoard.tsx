'use client'

/**
 * TravelBoard - Main Canvas Component for Trip Visualization (Issue #14)
 *
 * This is the primary export for the travel board canvas.
 * Wraps BoardWrapper with a cleaner API name.
 *
 * Features:
 * - Excalidraw canvas with travel-optimized settings
 * - Auto-save with 2s debounce
 * - Image hydration from URLs via proxy
 * - Export functionality enabled
 */

import BoardWrapper from './BoardWrapper'

export interface TravelBoardProps {
  /** The trip ID to load/save canvas state for */
  tripId?: string
  /** Enable read-only mode (no editing) */
  readOnly?: boolean
}

/**
 * TravelBoard Component
 *
 * Renders an interactive Excalidraw canvas for trip planning visualization.
 *
 * @example
 * ```tsx
 * <TravelBoard tripId="abc-123" />
 * ```
 */
export default function TravelBoard({ tripId, readOnly = false }: TravelBoardProps) {
  return <BoardWrapper tripId={tripId} readOnly={readOnly} />
}

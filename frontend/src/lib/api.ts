/**
 * API wrapper for backend communication
 */

import { supabase } from './supabase/client'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || ''

/**
 * Get auth headers with user ID
 */
async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`
  }
  return headers
}

interface ChatRequest {
  message: string
  history: Array<{ role: string; content: string }>
}

/**
 * Send a chat message to the backend
 */
export async function sendChatMessage(request: ChatRequest): Promise<Response> {
  const headers = await getAuthHeaders()
  return fetch(`${BACKEND_URL}/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  })
}

/**
 * Health check for backend
 */
export async function checkBackendHealth(): Promise<{ status: string }> {
  const response = await fetch(`${BACKEND_URL}/health`)
  return response.json()
}

/**
 * Canvas/Trip API
 */

export interface CanvasState {
  trip_id: string
  elements: unknown[]
  files: Record<string, unknown>
  appState?: Record<string, unknown> | null
  last_modified?: string | null
}

/**
 * Get canvas state for a trip
 */
export async function getCanvasState(tripId: string): Promise<CanvasState> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/trips/${tripId}/canvas`, { headers })
  if (!response.ok) {
    throw new Error(`Failed to load canvas: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Save canvas state for a trip
 */
export async function saveCanvasState(
  tripId: string,
  elements: unknown[],
  files: Record<string, unknown>,
  appState?: Record<string, unknown>
): Promise<CanvasState> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/trips/${tripId}/canvas`, {
    method: 'PUT',
    headers,
    body: JSON.stringify({ elements, files, appState }),
  })
  if (!response.ok) {
    throw new Error(`Failed to save canvas: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Get the latest trip ID
 */
export interface LatestTripResponse {
  trip_id: string
  title: string
  created_at: string | null
}

export async function getLatestTrip(): Promise<LatestTripResponse> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/trips/latest/id`, { headers })
  if (!response.ok) {
    throw new Error(`No trips found`)
  }
  return response.json()
}

/**
 * Dashboard API (Wave 4 - Issue #15)
 */

export interface TripListItem {
  id: string
  title: string
  status: string
  destination: string | null
  created_at: string | null
  updated_at: string | null
  thumbnail_url: string | null
}

export interface TripListResponse {
  trips: TripListItem[]
  count: number
}

/**
 * Get all trips for the dashboard
 */
export async function getTrips(): Promise<TripListResponse> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/trips`, { headers })
  if (!response.ok) {
    throw new Error(`Failed to fetch trips: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Update trip metadata (rename, etc.)
 */
export async function updateTrip(
  tripId: string,
  data: { title?: string; destination?: string; status?: string }
): Promise<{ id: string; title: string; status: string }> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/trips/${tripId}`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`Failed to update trip: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Delete a trip
 */
export async function deleteTrip(tripId: string): Promise<{ message: string; id: string }> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/trips/${tripId}`, {
    method: 'DELETE',
    headers,
  })
  if (!response.ok) {
    throw new Error(`Failed to delete trip: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Create a new trip
 */
export async function createTrip(data: { title?: string; destination?: string | null }): Promise<{ id: string; title: string; status: string }> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/trips`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error(`Failed to create trip: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Budget API (Issue #19)
 */

export interface BudgetItem {
  name: string
  type: string
  price: number
}

export interface BudgetResponse {
  budget: number | null
  spent: number
  items: BudgetItem[]
}

export async function getBudget(tripId: string): Promise<BudgetResponse> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/trips/${tripId}/budget`, { headers })
  if (!response.ok) {
    throw new Error(`Failed to fetch budget: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Share API (Issue #20)
 */

export async function shareTrip(tripId: string): Promise<{ share_token: string }> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/trips/${tripId}/share`, {
    method: 'POST',
    headers,
  })
  if (!response.ok) {
    throw new Error(`Failed to share trip: ${response.statusText}`)
  }
  return response.json()
}

export interface PublicBoardResponse {
  trip_id: string
  title: string
  elements: unknown[]
  files: Record<string, unknown>
}

export async function getPublicBoard(shareToken: string): Promise<PublicBoardResponse> {
  const response = await fetch(`${BACKEND_URL}/trips/public/${shareToken}`)
  if (!response.ok) {
    throw new Error(`Board not found`)
  }
  return response.json()
}

/**
 * Canvas Image Upload (Supabase Storage)
 *
 * Uploads a user-added image (base64 data URL) to Supabase Storage
 * and returns the public URL to store in scene_files instead of the base64.
 */

/** Convert a base64 data URL to a Blob */
function dataUrlToBlob(dataUrl: string): { blob: Blob; mimeType: string; ext: string } {
  const [header, base64] = dataUrl.split(',')
  const mimeType = header.match(/:(.*?);/)?.[1] || 'image/png'
  const ext = mimeType.split('/')[1]?.replace('jpeg', 'jpg') || 'png'
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return { blob: new Blob([bytes], { type: mimeType }), mimeType, ext }
}

/** Max file size for user uploads (5 MB) */
const MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024

/**
 * Upload a single canvas image to Supabase Storage.
 * Returns the public URL on success, or null on failure.
 */
export async function uploadCanvasImage(
  tripId: string,
  fileId: string,
  dataUrl: string
): Promise<string | null> {
  try {
    const { blob, mimeType, ext } = dataUrlToBlob(dataUrl)

    if (blob.size > MAX_IMAGE_SIZE_BYTES) {
      console.warn(`[Upload] File ${fileId} exceeds 5 MB limit (${(blob.size / 1024 / 1024).toFixed(1)} MB), skipping`)
      return null
    }

    const path = `${tripId}/${fileId}.${ext}`

    const { error } = await supabase.storage
      .from('canvas-images')
      .upload(path, blob, { contentType: mimeType, upsert: true })

    if (error) {
      console.error(`[Upload] Failed to upload ${fileId}:`, error.message)
      return null
    }

    // Build public URL
    const publicUrl = `${SUPABASE_URL}/storage/v1/object/public/canvas-images/${path}`
    console.log(`[Upload] Uploaded ${fileId} → ${publicUrl}`)
    return publicUrl
  } catch (err) {
    console.error(`[Upload] Error uploading ${fileId}:`, err)
    return null
  }
}

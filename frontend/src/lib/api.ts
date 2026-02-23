/**
 * API wrapper for backend communication
 */

import { supabase } from './supabase/client'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

/**
 * Get auth headers with user ID
 */
async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (session?.user?.id) {
    headers['X-User-ID'] = session.user.id
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
 * Submit user feedback
 */
export async function submitFeedback(feedback: string, username: string): Promise<{ status: string; id: string }> {
  const headers = await getAuthHeaders()
  const response = await fetch(`${BACKEND_URL}/feedback`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ feedback, username }),
  })
  if (!response.ok) {
    throw new Error(`Failed to submit feedback: ${response.statusText}`)
  }
  return response.json()
}

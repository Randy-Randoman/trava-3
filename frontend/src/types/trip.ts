/**
 * TypeScript interfaces for Trip data
 */

export interface Stop {
  id: string
  name: string
  location: string
  date: string
  duration: string
  notes?: string
}

export interface Stay {
  id: string
  name: string
  type: 'hotel' | 'airbnb' | 'hostel' | 'other'
  location: string
  checkIn: string
  checkOut: string
  price?: number
  currency?: string
  bookingUrl?: string
}

export interface Activity {
  id: string
  name: string
  description?: string
  location: string
  date: string
  time?: string
  duration?: string
  price?: number
  currency?: string
  category: 'sightseeing' | 'food' | 'adventure' | 'relaxation' | 'culture' | 'other'
}

export interface Trip {
  id: string
  name: string
  destination: string
  startDate: string
  endDate: string
  budget?: number
  currency?: string
  travelers: number
  vibe?: string
  stops: Stop[]
  stays: Stay[]
  activities: Activity[]
  createdAt: string
  updatedAt: string
}

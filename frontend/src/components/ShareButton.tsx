'use client'

import { useState } from 'react'
import { shareTrip } from '@/lib/api'

interface ShareButtonProps {
  tripId: string
}

export default function ShareButton({ tripId }: ShareButtonProps) {
  const [state, setState] = useState<'idle' | 'loading' | 'copied'>('idle')

  async function handleShare() {
    if (state === 'loading') return
    setState('loading')

    try {
      // 1. Dispatch flush-canvas so BoardWrapper saves latest state
      window.dispatchEvent(new CustomEvent('flush-canvas'))

      // 2. Wait for canvas-flushed event (with 3s timeout)
      await new Promise<void>((resolve) => {
        const timeout = setTimeout(() => {
          window.removeEventListener('canvas-flushed', handler)
          resolve()
        }, 3000)

        function handler() {
          clearTimeout(timeout)
          window.removeEventListener('canvas-flushed', handler)
          resolve()
        }

        window.addEventListener('canvas-flushed', handler)
      })

      // 3. Call shareTrip API
      const { share_token } = await shareTrip(tripId)

      // 4. Build share URL and copy to clipboard
      const shareUrl = `${window.location.origin}/board/${share_token}`
      await navigator.clipboard.writeText(shareUrl)

      // 5. Show "Copied!" confirmation
      setState('copied')
      setTimeout(() => setState('idle'), 2000)
    } catch (err) {
      console.error('Failed to share trip:', err)
      alert('Failed to share trip. Please try again.')
      setState('idle')
    }
  }

  return (
    <button
      onClick={handleShare}
      disabled={state === 'loading'}
      className="px-3 py-1.5 text-xs font-bold bg-white border-2 border-trava-black text-trava-black transition-all hover:bg-adventure-orange hover:shadow-brutal hover:translate-x-[-1px] hover:translate-y-[-1px] disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {state === 'loading' && 'Sharing...'}
      {state === 'copied' && 'Copied!'}
      {state === 'idle' && (
        <>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5"
          >
            <path d="M13 4.5a2.5 2.5 0 1 1 .702 1.737L6.97 9.604a2.5 2.5 0 0 1 0 .792l6.733 3.367a2.5 2.5 0 1 1-.671 1.341l-6.733-3.367a2.5 2.5 0 1 1 0-3.474l6.733-3.367A2.5 2.5 0 0 1 13 4.5Z" />
          </svg>
          Share
        </>
      )}
    </button>
  )
}

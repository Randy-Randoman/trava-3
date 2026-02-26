'use client'

/**
 * ShareButton - Generate and copy a public read-only board link (Issue #20)
 */

import { useState } from 'react'
import { shareTrip } from '@/lib/api'

interface ShareButtonProps {
  tripId: string
}

export default function ShareButton({ tripId }: ShareButtonProps) {
  const [shareUrl, setShareUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [open, setOpen] = useState(false)

  const handleShare = async () => {
    if (shareUrl) {
      setOpen(true)
      return
    }
    setLoading(true)
    try {
      const { share_token } = await shareTrip(tripId)
      const url = `${window.location.origin}/board/${share_token}`
      setShareUrl(url)
      setOpen(true)
    } catch {
      alert('Failed to generate share link. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async () => {
    if (!shareUrl) return
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback: select the input text
    }
  }

  return (
    <>
      {/* Share button */}
      <button
        onClick={handleShare}
        disabled={loading}
        title="Share board"
        className="absolute top-4 right-4 z-30 flex items-center gap-1.5 px-3 py-1.5 bg-retro-cream border-2 border-trava-black text-trava-black text-xs font-bold uppercase tracking-wide shadow-[3px_3px_0px_#1A1A1B] hover:translate-x-[-1px] hover:translate-y-[-1px] hover:shadow-[4px_4px_0px_#1A1A1B] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
          <path d="M13 4.5a2.5 2.5 0 1 1 .702 1.737L6.97 9.604a2.518 2.518 0 0 1 0 .792l6.733 3.367a2.5 2.5 0 1 1-.671 1.341l-6.733-3.367a2.5 2.5 0 1 1 0-3.474l6.733-3.366A2.52 2.52 0 0 1 13 4.5Z" />
        </svg>
        {loading ? 'Sharing…' : 'Share'}
      </button>

      {/* Share modal */}
      {open && shareUrl && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />

          {/* Modal */}
          <div className="relative bg-retro-cream border-4 border-trava-black shadow-[8px_8px_0px_#1A1A1B] w-full max-w-md mx-4">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b-4 border-trava-black">
              <h2 className="text-lg font-black uppercase tracking-tight text-trava-black">Share Board</h2>
              <button
                onClick={() => setOpen(false)}
                className="p-1 text-trava-black hover:text-adventure-orange transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                  <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
                </svg>
              </button>
            </div>

            {/* Body */}
            <div className="p-4 space-y-3">
              <p className="text-sm text-gray-600 font-medium">
                Anyone with this link can view your board in read-only mode.
              </p>
              <div className="flex gap-2">
                <input
                  readOnly
                  value={shareUrl}
                  className="flex-1 bg-white border-2 border-trava-black px-3 py-2 text-xs font-mono text-trava-black focus:outline-none"
                  onClick={e => (e.target as HTMLInputElement).select()}
                />
                <button
                  onClick={handleCopy}
                  className="px-3 py-2 bg-trava-teal border-2 border-trava-black text-trava-black text-xs font-bold uppercase tracking-wide transition-all hover:shadow-[3px_3px_0px_#1A1A1B] hover:translate-x-[-1px] hover:translate-y-[-1px]"
                >
                  {copied ? '✓ Copied' : 'Copy'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

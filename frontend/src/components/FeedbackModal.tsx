'use client'

import { useState } from 'react'
import { submitFeedback } from '@/lib/api'

interface FeedbackModalProps {
  userEmail: string
  onClose: () => void
}

export default function FeedbackModal({ userEmail, onClose }: FeedbackModalProps) {
  const [text, setText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async () => {
    if (!text.trim()) return
    setSubmitting(true)
    try {
      await submitFeedback(text.trim(), userEmail)
      setSubmitted(true)
      setTimeout(() => onClose(), 1500)
    } catch (err) {
      alert('Failed to submit feedback. Please try again.')
      console.error(err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-retro-cream border-4 border-trava-black shadow-[8px_8px_0px_#1A1A1B] w-full max-w-lg mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b-4 border-trava-black">
          <h2 className="text-xl font-black uppercase tracking-tight text-trava-black">Write Feedback</h2>
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
          {submitted ? (
            <div className="text-center py-8">
              <div className="w-14 h-14 bg-trava-teal border-2 border-trava-black flex items-center justify-center mx-auto mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-8 h-8 text-trava-black">
                  <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 0 1 .143 1.052l-8 10.5a.75.75 0 0 1-1.127.075l-4.5-4.5a.75.75 0 0 1 1.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 0 1 1.05-.143Z" clipRule="evenodd" />
                </svg>
              </div>
              <p className="font-black text-trava-black uppercase">Thank you!</p>
              <p className="text-sm text-gray-500 mt-1">Your feedback has been submitted.</p>
            </div>
          ) : (
            <>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value.slice(0, 1000))}
                placeholder="Tell us what you think — bugs, ideas, or anything else..."
                rows={6}
                className="w-full bg-white border-2 border-trava-black px-4 py-3 text-sm font-medium text-trava-black placeholder:text-gray-400 focus:outline-none focus:shadow-brutal transition-all resize-none"
              />
              <div className="flex items-center justify-between mt-3">
                <span className="text-xs font-bold text-gray-400">
                  {text.length}/1000
                </span>
                <button
                  onClick={handleSubmit}
                  disabled={submitting || !text.trim()}
                  className="px-6 py-2.5 bg-adventure-orange border-2 border-trava-black text-trava-black font-black text-sm uppercase tracking-wide
                    transition-all hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[4px_4px_0px_#1A1A1B]
                    active:translate-x-[1px] active:translate-y-[1px] active:shadow-none
                    disabled:bg-gray-300 disabled:cursor-not-allowed disabled:border-gray-400 disabled:shadow-none"
                >
                  {submitting ? 'Submitting...' : 'Submit Feedback'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

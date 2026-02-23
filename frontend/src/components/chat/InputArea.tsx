'use client'

import { useState, KeyboardEvent } from 'react'

interface InputAreaProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function InputArea({ onSend, disabled }: InputAreaProps) {
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim())
      setInput('')
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="border-t-4 border-trava-black p-4 bg-retro-cream">
      <div className="flex items-end gap-3">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Tell me about your dream trip..."
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none bg-white border-2 border-trava-black px-4 py-3 text-sm font-medium text-trava-black placeholder:text-gray-400 focus:outline-none focus:bg-white focus:brutal-shadow transition-all disabled:bg-gray-100 disabled:text-gray-400"
          style={{ minHeight: '52px', maxHeight: '120px' }}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="h-[52px] px-6 bg-adventure-orange border-2 border-trava-black text-trava-black transition-all hover:translate-x-[-1px] hover:translate-y-[-1px] hover:shadow-[3px_3px_0px_#1A1A1B] active:translate-x-[1px] active:translate-y-[1px] active:shadow-none disabled:bg-gray-300 disabled:cursor-not-allowed disabled:border-gray-400 disabled:shadow-none"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
            <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
          </svg>
        </button>
      </div>
    </div>
  )
}

'use client'

import { useRef, useEffect } from 'react'
import { ChatBubble } from './ChatBubble'
import { InputArea } from './InputArea'
import { ThinkingIndicator } from './ThinkingIndicator'
import { StatusToast } from './StatusToast'
import { useChat } from '@/lib/hooks/useChat'
import ShareButton from '@/components/ShareButton'

interface ChatInterfaceProps {
  tripId?: string  // Current trip ID
  onDashboard?: () => void
}

export function ChatInterface({ tripId, onDashboard }: ChatInterfaceProps) {
  const { messages, isLoading, status, boardReady, sendMessage } = useChat({
    tripId: tripId || ''  // Pass tripId to useChat
  })
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div className="flex flex-col h-full">
      {/* Status Toast */}
      <StatusToast message={status} visible={!!status && isLoading} />

      {/* Header */}
      <div className="p-4 border-b-4 border-trava-black bg-retro-cream flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <img src="/trava-logo.png" alt="Trava Logo" className="h-8 w-auto object-contain " />
          <div>
            <h1 className="text-xl font-black uppercase tracking-tighter text-trava-black leading-none">TRAVA</h1>
            <p className="text-xs font-bold text-gray-500">AI Travel Assistant</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {tripId && <ShareButton tripId={tripId} />}
          {onDashboard && (
            <button
              onClick={onDashboard}
              className="px-3 py-1.5 text-xs font-bold bg-white border-2 border-trava-black text-trava-black transition-all hover:bg-adventure-orange hover:shadow-brutal hover:translate-x-[-1px] hover:translate-y-[-1px]"
            >
              Dashboard
            </button>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 bg-white/50">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-trava-teal border-2 border-trava-black flex items-center justify-center mb-4 brutal-shadow">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8 text-trava-black">
                <path fillRule="evenodd" d="M8.161 2.58a1.875 1.875 0 0 1 1.678 0l4.993 2.498c.106.052.23.052.336 0l3.869-1.935A1.875 1.875 0 0 1 21.75 4.82v12.485c0 .71-.401 1.36-1.037 1.677l-4.875 2.437a1.875 1.875 0 0 1-1.676 0l-4.994-2.497a.375.375 0 0 0-.336 0l-3.868 1.935A1.875 1.875 0 0 1 2.25 19.18V6.695c0-.71.401-1.36 1.036-1.677l4.875-2.438ZM9 6a.75.75 0 0 1 .75.75V15a.75.75 0 0 1-1.5 0V6.75A.75.75 0 0 1 9 6Zm6.75 3a.75.75 0 0 0-1.5 0v8.25a.75.75 0 0 0 1.5 0V9Z" clipRule="evenodd" />
              </svg>
            </div>
            <h2 className="text-xl font-black text-trava-black mb-2 uppercase">Welcome to TRAVA!</h2>
            <p className="text-gray-500 text-sm max-w-xs font-medium">
              Tell me about your dream trip and I&apos;ll help you plan the perfect itinerary.
            </p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatBubble key={message.id} message={message} />
            ))}
            {isLoading && <ThinkingIndicator status={status} />}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Create Board Button */}
      {boardReady && !isLoading && (
        <div className="px-4 py-3 bg-retro-cream border-t-2 border-trava-black">
          <button
            onClick={() => sendMessage('Create the board')}
            className="w-full py-3 px-6 bg-trava-teal border-2 border-trava-black text-trava-black font-black text-sm uppercase tracking-wide
              transition-all hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[4px_4px_0px_#1A1A1B]
              active:translate-x-[1px] active:translate-y-[1px] active:shadow-none
              flex items-center justify-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
              <path fillRule="evenodd" d="M8.161 2.58a1.875 1.875 0 0 1 1.678 0l4.993 2.498c.106.052.23.052.336 0l3.869-1.935A1.875 1.875 0 0 1 21.75 4.82v12.485c0 .71-.401 1.36-1.037 1.677l-4.875 2.437a1.875 1.875 0 0 1-1.676 0l-4.994-2.497a.375.375 0 0 0-.336 0l-3.868 1.935A1.875 1.875 0 0 1 2.25 19.18V6.695c0-.71.401-1.36 1.036-1.677l4.875-2.438ZM9 6a.75.75 0 0 1 .75.75V15a.75.75 0 0 1-1.5 0V6.75A.75.75 0 0 1 9 6Zm6.75 3a.75.75 0 0 0-1.5 0v8.25a.75.75 0 0 0 1.5 0V9Z" clipRule="evenodd" />
            </svg>
            Create Travel Board
          </button>
        </div>
      )}

      {/* Input Area */}
      <InputArea onSend={sendMessage} disabled={isLoading} />
    </div>
  )
}

'use client'

import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Message } from '@/types'

interface ChatBubbleProps {
  message: Message
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div
        className={`max-w-[85%] px-5 py-4 border-2 border-trava-black shadow-brutal ${isUser
          ? 'bg-trava-teal-light text-trava-black'
          : 'bg-adventure-orange-light text-trava-black'
          }`}
      >
        <div className="text-sm md:text-base font-medium leading-relaxed">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ node, ...props }: any) => <p className="mb-2 last:mb-0" {...props} />,
              ul: ({ node, ...props }: any) => <ul className="list-disc pl-4 mb-2 space-y-1" {...props} />,
              ol: ({ node, ...props }: any) => <ol className="list-decimal pl-4 mb-2 space-y-1" {...props} />,
              li: ({ node, ...props }: any) => <li className="marker:text-trava-black" {...props} />,
              a: ({ node, ...props }: any) => <a className="underline decoration-2 underline-offset-2 hover:text-adventure-orange transition-colors" target="_blank" rel="noopener noreferrer" {...props} />,
              code: ({ node, ...props }: any) => <code className="bg-black/10 px-1 py-0.5 rounded font-mono text-xs" {...props} />,
              strong: ({ node, ...props }: any) => <strong className="font-extrabold text-trava-black" {...props} />,
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        <span className={`text-xs mt-2 block font-bold uppercase opacity-60 ${isUser ? 'text-trava-black' : 'text-gray-500'}`}>
          {isUser ? 'You' : 'Trava'} • {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  )
}

'use client'

import { useState, useCallback, useEffect } from 'react'
import { Message } from '@/types'
import { supabase } from '@/lib/supabase/client'
import { env } from '@/lib/env'
import { parseSse } from '@/lib/sse'

interface UseChatOptions {
  tripId: string  // REQUIRED - conversation is linked to trip
}

export function useChat(options: UseChatOptions) {
  const { tripId } = options
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState('')
  const [boardReady, setBoardReady] = useState(false)

  // Load messages from database on mount
  useEffect(() => {
    if (!tripId) return

    const loadMessages = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession()
        const headers: Record<string, string> = {}
        if (session?.access_token) {
          headers['Authorization'] = `Bearer ${session.access_token}`
        }
        const response = await fetch(`${env.backendUrl()}/chat/messages/${tripId}`, { headers })

        if (!response.ok) {
          // No history available — start with empty messages
          return
        }

        const data = await response.json()
        const loadedMessages: Message[] = data.messages.map((msg: any, index: number) => ({
          id: `${msg.role}-${index}`,
          role: msg.role === 'model' ? 'assistant' : msg.role,  // Convert 'model' to 'assistant' for UI
          content: msg.content,
          timestamp: msg.created_at,
        }))

        setMessages(loadedMessages)
      } catch (error) {
        console.error('Failed to load messages:', error)
      }
    }

    loadMessages()
  }, [tripId])

  const sendMessage = useCallback(async (content: string) => {
    // Create user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }

    // Add user message immediately (optimistic update)
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)
    setStatus('Thinking...')

    try {
      // NO history sent - backend loads from database!
      // Call the streaming endpoint
      const { data: { session } } = await supabase.auth.getSession()
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`
      }
      const response = await fetch(`${env.backendUrl()}/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          trip_id: tripId,
          message: content,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No response body')
      }

      let assistantContent = ''
      const assistantMessageId = `assistant-${Date.now()}`

      // Process the stream; partial lines are carried over to the next read
      let rest = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const parsed = parseSse(rest, decoder.decode(value, { stream: true }))
        rest = parsed.rest

        for (const data of parsed.events) {
          if (data.type === 'status') {
            setStatus(data.content)
          } else if (data.type === 'text') {
            assistantContent = data.content

            // Add or update assistant message
            setMessages((prev) => {
              const existing = prev.find((m) => m.id === assistantMessageId)
              if (existing) {
                return prev.map((m) =>
                  m.id === assistantMessageId
                    ? { ...m, content: assistantContent }
                    : m
                )
              }
              return [
                ...prev,
                {
                  id: assistantMessageId,
                  role: 'assistant',
                  content: assistantContent,
                  timestamp: new Date().toISOString(),
                } as Message,
              ]
            })
          } else if (data.type === 'canvas_updated') {
            // Canvas already updated server-side. Just reload.
            window.dispatchEvent(new CustomEvent('canvas-updated', { detail: { tripId } }))
          } else if (data.type === 'board_ready') {
            setBoardReady(true)
          } else if (data.type === 'done') {
            setStatus('')
          } else if (data.type === 'error') {
            throw new Error(data.content)
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error)

      // Add error message
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date().toISOString(),
        } as Message,
      ])
    } finally {
      setIsLoading(false)
      setStatus('')
    }
  }, [tripId])  // Dependency on tripId, not messages

  return {
    messages,
    isLoading,
    status,
    boardReady,
    sendMessage,
  }
}

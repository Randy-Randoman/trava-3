'use client'

import { useState, useCallback, useEffect } from 'react'
import { Message } from '@/types'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

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
        console.log(`📥 [Chat] Loading messages for trip: ${tripId}`)
        const response = await fetch(`${BACKEND_URL}/chat/messages/${tripId}`)

        if (!response.ok) {
          // Chat endpoint may not be implemented yet (501) — just start with empty messages
          console.log(`[Chat] Messages endpoint returned ${response.status}, starting fresh`)
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
        console.log(`✅ [Chat] Loaded ${loadedMessages.length} messages`)
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
      console.log(`📝 [Chat] Sending message for trip: ${tripId}`)

      // Call the streaming endpoint
      const response = await fetch(`${BACKEND_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          trip_id: tripId,  // NEW - send trip_id instead of history
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

      // Process the stream
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

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
                console.log('✅ Board ready signal received')
                setBoardReady(true)
              } else if (data.type === 'done') {
                setStatus('')
              } else if (data.type === 'error') {
                throw new Error(data.content)
              }
            } catch (e) {
              // Ignore JSON parse errors for incomplete chunks
            }
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

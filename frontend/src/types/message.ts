/**
 * TypeScript interfaces for Chat/Message data
 */

export type MessageRole = 'user' | 'assistant' | 'system'

export interface Message {
  id: string
  role: MessageRole
  content: string
  timestamp: string
  status?: 'sending' | 'sent' | 'error'
}

export interface ChatHistory {
  messages: Message[]
  sessionId: string
  createdAt: string
}

export interface StreamChunk {
  type: 'text' | 'status' | 'board_data' | 'error'
  content: string
}

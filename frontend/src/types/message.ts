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

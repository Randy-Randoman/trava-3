'use client'

interface ThinkingIndicatorProps {
  status?: string
}

export function ThinkingIndicator({ status }: ThinkingIndicatorProps) {
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          {status && (
            <span className="text-xs text-gray-500 ml-2">{status}</span>
          )}
        </div>
      </div>
    </div>
  )
}

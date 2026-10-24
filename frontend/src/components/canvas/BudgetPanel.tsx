'use client'

/**
 * BudgetPanel - Floating budget overlay on the trip board
 *
 * Shows total spent vs. trip budget. Refreshes on canvas-updated events.
 */

import { useEffect, useState, useCallback } from 'react'
import { getBudget, BudgetResponse } from '@/lib/api'

interface BudgetPanelProps {
  tripId: string
}

export default function BudgetPanel({ tripId }: BudgetPanelProps) {
  const [data, setData] = useState<BudgetResponse | null>(null)
  const [collapsed, setCollapsed] = useState(false)

  const fetchBudget = useCallback(async () => {
    try {
      const result = await getBudget(tripId)
      setData(result)
    } catch {
      // Silently ignore — board may have no items yet
    }
  }, [tripId])

  // Fetch on mount and whenever the canvas is updated (by agent or user save)
  useEffect(() => {
    fetchBudget()
    const handleRefresh = () => fetchBudget()
    window.addEventListener('canvas-updated', handleRefresh)
    window.addEventListener('canvas-saved', handleRefresh)
    return () => {
      window.removeEventListener('canvas-updated', handleRefresh)
      window.removeEventListener('canvas-saved', handleRefresh)
    }
  }, [fetchBudget])

  // Don't render if there's nothing to show
  if (!data || (data.spent === 0 && data.budget === null)) return null

  const { budget, spent } = data
  const pct = budget && budget > 0 ? Math.min((spent / budget) * 100, 100) : null
  const over = budget !== null && spent > budget

  return (
    <div className="absolute bottom-4 left-4 z-30 bg-retro-cream border-2 border-trava-black shadow-[4px_4px_0px_#1A1A1B] w-56 select-none">
      {/* Header */}
      <button
        className="w-full flex items-center justify-between px-3 py-2 border-b-2 border-trava-black hover:bg-gray-100 transition-colors"
        onClick={() => setCollapsed(c => !c)}
      >
        <span className="font-black text-xs uppercase tracking-wide text-trava-black">
          Budget
        </span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className={`w-4 h-4 text-trava-black transition-transform ${collapsed ? 'rotate-180' : ''}`}
        >
          <path fillRule="evenodd" d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z" clipRule="evenodd" />
        </svg>
      </button>

      {!collapsed && (
        <div className="px-3 py-2 space-y-2">
          {/* Item list */}
          {data.items.length > 0 && (
            <ul className="space-y-1 max-h-48 overflow-y-auto">
              {data.items.map((item, i) => (
                <li key={i} className="flex items-baseline justify-between text-xs">
                  <span className="text-gray-700 truncate mr-2">{item.name}</span>
                  <span className="text-trava-black font-bold whitespace-nowrap">
                    €{item.price.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </span>
                </li>
              ))}
            </ul>
          )}

          {/* Divider */}
          {data.items.length > 0 && (
            <div className="border-t border-gray-300" />
          )}

          {/* Spent line */}
          <div className="flex items-baseline justify-between">
            <span className="text-xs text-gray-500 font-medium">Total</span>
            <span className={`text-sm font-black ${over ? 'text-red-600' : 'text-trava-black'}`}>
              €{spent.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </span>
          </div>

          {/* Budget line (only if set) */}
          {budget !== null && (
            <div className="flex items-baseline justify-between">
              <span className="text-xs text-gray-500 font-medium">Budget</span>
              <span className="text-sm font-black text-trava-black">
                €{budget.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </span>
            </div>
          )}

          {/* Progress bar */}
          {pct !== null && (
            <div className="w-full bg-gray-200 border border-trava-black h-2">
              <div
                className={`h-full transition-all ${over ? 'bg-red-500' : 'bg-trava-teal'}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          )}

          {/* Over-budget warning */}
          {over && budget !== null && (
            <p className="text-xs font-bold text-red-600">
              €{(spent - budget).toLocaleString(undefined, { maximumFractionDigits: 0 })} over budget
            </p>
          )}
        </div>
      )}
    </div>
  )
}

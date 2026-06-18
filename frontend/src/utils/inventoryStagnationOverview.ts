import type { InventoryStagnationResponse, InventoryStagnationRow } from '@/api/database'
import { inventoryColumnLabel } from '@/views/erp/production/planning/components/inventoryStagnationConstants'

export interface InventoryStagnationHeaderOverview {
  count: number
  processCount: number
  as_of: string
  min_quantity: number
  stable_calendar_days: number
  period_start: string
  period_end: string
  topProcesses: Array<{ column: string; label: string; count: number }>
}

export const INVENTORY_STAGNATION_DEFAULT_MIN_QTY = 50
export const INVENTORY_STAGNATION_DEFAULT_STABLE_DAYS = 7

function todayJstIsoDate() {
  const now = new Date()
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000)
  const y = jst.getUTCFullYear()
  const m = String(jst.getUTCMonth() + 1).padStart(2, '0')
  const d = String(jst.getUTCDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function summarizeProcessCounts(rows: InventoryStagnationRow[]) {
  const map = new Map<string, number>()
  for (const row of rows) {
    map.set(row.inventory_column, (map.get(row.inventory_column) || 0) + 1)
  }
  return [...map.entries()]
    .map(([column, count]) => ({
      column,
      label: inventoryColumnLabel(column),
      count,
    }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, 'ja'))
}

export function parseInventoryStagnationOverview(
  raw: unknown,
  fallbackAsOf = todayJstIsoDate(),
): InventoryStagnationHeaderOverview | null {
  const payload = (raw as { data?: InventoryStagnationResponse['data'] })?.data
    ?? (raw as InventoryStagnationResponse['data'] | undefined)
  if (!payload || !Array.isArray(payload.list)) return null

  const list = payload.list
  if (!list.length) return null

  const topProcesses = summarizeProcessCounts(list)
  return {
    count: list.length,
    processCount: topProcesses.length,
    as_of: payload.as_of || fallbackAsOf,
    min_quantity: payload.min_quantity ?? INVENTORY_STAGNATION_DEFAULT_MIN_QTY,
    stable_calendar_days: payload.stable_calendar_days ?? INVENTORY_STAGNATION_DEFAULT_STABLE_DAYS,
    period_start: payload.period_start || '',
    period_end: payload.period_end || '',
    topProcesses: topProcesses.slice(0, 4),
  }
}

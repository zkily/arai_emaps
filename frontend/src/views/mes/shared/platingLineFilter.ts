import type { PlatingProductionIndicatorLineOption } from '@/api/platingProductionIndicator'
import { fetchPlatingProductionIndicatorLines } from '@/api/platingProductionIndicator'

export type PlatingLineOption = PlatingProductionIndicatorLineOption

export async function loadPlatingLineOptions(params: {
  start_date: string
  end_date: string
}): Promise<PlatingLineOption[]> {
  const res = await fetchPlatingProductionIndicatorLines(params)
  const lines = res.data ?? []
  if (lines.length > 0) return lines
  return [{ line_name: 'メッキ工程' }]
}

export function lineLabel(line: PlatingLineOption | string): string {
  if (typeof line === 'string') return line.trim() || '—'
  return (line.line_name || '').trim() || '—'
}

export function resolvePlatingMetricsLabel(code: string, _map: Map<string, string>): string {
  return code
}

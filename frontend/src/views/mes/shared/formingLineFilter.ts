import type { FormingProductionIndicatorLineOption } from '@/api/formingProductionIndicator'
import { fetchFormingProductionIndicatorLines } from '@/api/formingProductionIndicator'

export async function loadFormingLineOptions(params: {
  start_date: string
  end_date: string
}): Promise<FormingProductionIndicatorLineOption[]> {
  const res = await fetchFormingProductionIndicatorLines(params)
  return res.data ?? []
}

export function lineLabel(line: FormingProductionIndicatorLineOption): string {
  return (line.line_name || '').trim() || '—'
}

export function resolveFormingMetricsLabel(code: string, _map: Map<string, string>): string {
  return code
}

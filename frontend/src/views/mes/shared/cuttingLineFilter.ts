import type { CuttingProductionIndicatorLineOption } from '@/api/cuttingProductionIndicator'
import { fetchCuttingProductionIndicatorLines } from '@/api/cuttingProductionIndicator'

export async function loadCuttingLineOptions(params: {
  start_date: string
  end_date: string
}): Promise<CuttingProductionIndicatorLineOption[]> {
  const res = await fetchCuttingProductionIndicatorLines(params)
  return res.data ?? []
}

export function lineLabel(line: CuttingProductionIndicatorLineOption): string {
  return (line.line_name || '').trim() || '—'
}

export function resolveCuttingMetricsLabel(code: string, _map: Map<string, string>): string {
  return code
}

import type { ChamferingProductionIndicatorLineOption } from '@/api/chamferingProductionIndicator'
import { fetchChamferingProductionIndicatorLines } from '@/api/chamferingProductionIndicator'

export async function loadChamferingLineOptions(params: {
  start_date: string
  end_date: string
}): Promise<ChamferingProductionIndicatorLineOption[]> {
  const res = await fetchChamferingProductionIndicatorLines(params)
  return res.data ?? []
}

export function lineLabel(line: ChamferingProductionIndicatorLineOption): string {
  return (line.line_name || '').trim() || '—'
}

export function resolveChamferingMetricsLabel(code: string, _map: Map<string, string>): string {
  return code
}

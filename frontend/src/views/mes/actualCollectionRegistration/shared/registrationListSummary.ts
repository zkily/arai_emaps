export interface RegistrationListSummary {
  totalProductionQty: number
  avgEfficiencyPerHour: number | null
}

/** 正味稼働秒（mes_net_production_sec のみ） */
export function getMesNetProductionSec(row: { mes_net_production_sec?: number | null }): number {
  const sec = row.mes_net_production_sec
  if (sec == null || !Number.isFinite(Number(sec))) return 0
  return Math.max(0, Math.round(Number(sec)))
}

/** 能率(個/時) = actual_production_quantity ÷ (mes_net_production_sec / 3600) */
export function efficiencyPerHourFromNetSec(
  actualQty: number | null | undefined,
  netSec: number | null | undefined,
): number | null {
  const prod = Number(actualQty ?? 0)
  const sec = Number(netSec ?? 0)
  if (!Number.isFinite(prod) || prod <= 0) return null
  if (!Number.isFinite(sec) || sec <= 0) return null
  const rate = prod / (sec / 3600)
  if (!Number.isFinite(rate)) return null
  return Math.round(rate)
}

export function buildRegistrationListSummary<T>(
  rows: T[],
  opts: {
    getQty: (row: T) => number
    isInProgress: (row: T) => boolean
    getNetSec: (row: T) => number
  },
): RegistrationListSummary {
  let totalQty = 0
  let effQty = 0
  let effNetSec = 0
  for (const row of rows) {
    const qty = opts.getQty(row)
    totalQty += qty
    if (opts.isInProgress(row) || qty <= 0) continue
    const netSec = opts.getNetSec(row)
    if (netSec <= 0) continue
    effQty += qty
    effNetSec += netSec
  }
  const avg =
    effQty > 0 && effNetSec > 0 ? Math.round(effQty / (effNetSec / 3600)) : null
  return { totalProductionQty: totalQty, avgEfficiencyPerHour: avg }
}

export function formatRegistrationListQty(qty: number): string {
  return qty.toLocaleString('ja-JP')
}

export function formatRegistrationListEfficiency(
  rate: number | null,
  unit: '本/時' | '個/時' = '本/時',
): string {
  return rate == null ? '—' : `${rate} ${unit}`
}

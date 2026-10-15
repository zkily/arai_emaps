/** 生産設備能力計算。可動率・合格率は画面上 0〜100%。 */

export type Judgment = 'ok' | 'ng' | null

export interface HeaderInput {
  regular_hours: number
  shift_count: number
  overtime_hours: number
  working_days: number
}

export interface LineInput {
  monthly_qty: number
  qty_days: number
  rate_per_hour: number
  availability_pct: number
  pass_rate_pct: number
  setup_hours: number
  actual_days: number
}

export interface HeaderCalc {
  daily_available: number
  total_hours: number
}

export interface LineCalc {
  daily_qty: number
  production_hours: number
  operating_hours: number
  weighted_hours: number
  occupied_hours: number
  rate_per_hour: number
  occupancy_pct: number | null
  daily_judgment: Judgment
}

export interface TotalCalc {
  item_count: number
  active_count: number
  total_hours: number
  daily_available: number
  production_hours: number
  operating_hours: number
  occupied_hours: number
  occupancy_pct: number | null
  remain_hours: number
  daily_judgment: Judgment
  month_judgment: Judgment
  peak_hourly: number
}

function n(value: unknown, fallback = 0): number {
  const x = Number(value)
  return Number.isFinite(x) ? x : fallback
}

export function calcHeader(input: HeaderInput): HeaderCalc {
  const regular = Math.max(n(input.regular_hours), 0)
  const shifts = Math.max(n(input.shift_count), 0)
  const overtime = Math.max(n(input.overtime_hours), 0)
  const days = Math.max(n(input.working_days), 0)
  const dailyAvailable = (regular + overtime) * shifts
  return { daily_available: dailyAvailable, total_hours: dailyAvailable * days }
}

export function calcLine(input: LineInput, header: HeaderCalc): LineCalc {
  const monthly = Math.max(n(input.monthly_qty), 0)
  const daysB = Math.max(n(input.qty_days), 0)
  const rate = Math.max(n(input.rate_per_hour), 0)
  const avail = n(input.availability_pct) / 100
  const pass = n(input.pass_rate_pct) / 100
  const setup = Math.max(n(input.setup_hours), 0)
  const actual = Math.max(n(input.actual_days), 0)
  const dailyQty = daysB > 0 ? monthly / daysB : 0
  const denom = rate * avail * pass
  const productionHours = dailyQty > 0 && denom > 0 ? dailyQty / denom : 0
  const operatingHours = productionHours > 0 ? productionHours + setup : 0
  const weightedHours = operatingHours > 0 && actual > 0 ? (daysB / actual) * productionHours + setup : 0
  const occupiedHours = actual > 0 ? weightedHours * actual : 0
  const occupancyPct = header.total_hours > 0 ? (occupiedHours / header.total_hours) * 100 : null
  let dailyJudgment: Judgment = null
  if (productionHours > 0 && header.daily_available > 0) {
    dailyJudgment = weightedHours > header.daily_available ? 'ng' : 'ok'
  }
  return {
    daily_qty: dailyQty,
    production_hours: productionHours,
    operating_hours: operatingHours,
    weighted_hours: weightedHours,
    occupied_hours: occupiedHours,
    rate_per_hour: rate,
    occupancy_pct: occupancyPct,
    daily_judgment: dailyJudgment,
  }
}

export function calcTotals(lines: LineCalc[], header: HeaderCalc): TotalCalc {
  let production = 0
  let operating = 0
  let occupied = 0
  let peak = 0
  let active = 0
  for (const line of lines) {
    if (line.production_hours > 0) active += 1
    production += line.production_hours
    operating += line.operating_hours
    occupied += line.occupied_hours
    peak = Math.max(peak, line.rate_per_hour)
  }
  const total = header.total_hours
  return {
    item_count: lines.length,
    active_count: active,
    total_hours: total,
    daily_available: header.daily_available,
    production_hours: production,
    operating_hours: operating,
    occupied_hours: occupied,
    occupancy_pct: total > 0 ? (occupied / total) * 100 : null,
    remain_hours: total - occupied,
    daily_judgment: active <= 0 ? null : operating > header.daily_available ? 'ng' : 'ok',
    month_judgment: active <= 0 ? null : total <= 0 || occupied > total ? 'ng' : 'ok',
    peak_hourly: peak,
  }
}

export function fmtNum(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) return '－'
  return value.toLocaleString('ja-JP', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

export function judgmentLabel(value: Judgment): string {
  if (value === 'ok') return '◎'
  if (value === 'ng') return '×'
  return '－'
}

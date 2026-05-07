/**
 * 月度工程別生産負荷サマリ API
 *
 * 対象月（YYYY-MM）について、内示・各工程の月計画数、能率、定時時間、所要時間、
 * 負荷率などを集計したデータを取得する。
 */
import request from '@/shared/api/request'

export interface MonthlyLoadForecastDaily {
  month_label: string
  year_month: string
  value_per_day: number | null
  working_days: number
  forecast_total: number
}

export interface MonthlyLoadHeader {
  year_month: string
  title_month: string
  working_days: number
  forecast_daily_next_months: MonthlyLoadForecastDaily[]
}

export interface MonthlyLoadRow {
  key: string
  label: string
  plan_qty: number | null
  plan_thousand: number | null
  plan_thousand_per_day: number | null
  resource_count: number | null
  resource_unit: string
  shift_count: number | null
  efficiency: number | null
  monthly_regular_hours: number | null
  required_hours: number | null
  load_pct: number | null
  daily_avg_hours: number | null
  annotation: string | null
  manual: boolean
}

export interface MonthlyLoadSummary {
  success?: boolean
  header: MonthlyLoadHeader
  rows: MonthlyLoadRow[]
  config_note?: string
  warnings?: string[]
  generated_at?: string
}

export async function fetchMonthlyLoadSummary(yearMonth: string): Promise<MonthlyLoadSummary> {
  const res = (await request.get<MonthlyLoadSummary>(
    '/api/production-monthly-load/summary',
    { params: { yearMonth } },
  )) as unknown as MonthlyLoadSummary
  return res
}

/**
 * 成型工程计划试算 API
 */
import request from '@/utils/request'

const BASE = '/api/database/forming-daily-plan'

export interface ProcessRunCalendarItem {
  process_key: string
  dates: string[]
}

export interface DailyPlanCell {
  molding_plan: number
  derived_plan: number
  final_plan?: number
  override_plan?: number | null
}

export interface DailyMatrixRow {
  product_cd: string
  process_key: string
  by_date: Record<string, DailyPlanCell>
}

export interface InventoryCell {
  simulated: number
  current: number
}

export interface InventoryMatrixRow {
  product_cd: string
  process_key: string
  by_date: Record<string, InventoryCell>
}

export interface OrderMatrixRow {
  product_cd: string
  process_key: string
  by_date: Record<string, number>
}

export interface ProcessPlanTotalItem {
  process_key: string
  total: number
  ratio_to_molding: number | null
  is_baseline: boolean
}

export interface ProcessPlanDailyTotalRow {
  process_key: string
  by_date: Record<string, number>
  total: number
}

export interface FormingPlanKpi {
  total_molding_plan: number
  negative_warehouse_days: number
  min_warehouse_inventory: number
  has_molding_plan: boolean
  product_count: number
  process_plan_totals?: ProcessPlanTotalItem[]
}

export interface FormingDailyPlanSummaryData {
  period: { start: string; end: string }
  dates: string[]
  products: {
    product_cd: string
    product_name?: string | null
    route_cd?: string
    machines?: Record<string, string>
    molding_order?: number | null
  }[]
  daily_matrix: { rows: DailyMatrixRow[] }
  order_matrix?: { rows: OrderMatrixRow[] }
  inventory_matrix: { rows: InventoryMatrixRow[] }
  trend_matrix?: { rows: { product_cd: string; process_key: string; by_date: Record<string, number> }[] }
  order_forecast?: OrderForecastMonth[]
  process_plan_totals?: ProcessPlanTotalItem[]
  process_plan_daily_totals?: ProcessPlanDailyTotalRow[]
  order_process_totals?: ProcessPlanTotalItem[]
  kpi: FormingPlanKpi
}

export interface OrderForecastMonth {
  year: number
  month: number
  source: 'order_monthly' | 'historical_avg' | 'pattern_only'
  daily: { date: string; forecast_units: number; order_units: number; weekday?: string }[]
  monthly_total: { forecast: number; order: number }
}

export interface FormingPlanScenario {
  id: number
  name: string
  period_start: string
  period_end: string
  base_month: string
  status: 'draft' | 'applied' | 'archived'
  created_by?: string | null
  applied_at?: string | null
  applied_by?: string | null
  created_at?: string
  updated_at?: string
}

export interface ScenarioPayload {
  include_forecast_months?: boolean
  process_overrides?: Record<string, Record<string, Record<string, number>>>
  run_calendar_snapshot?: ProcessRunCalendarItem[]
  notes?: string
  last_simulation?: FormingDailyPlanSummaryData
}

export interface SimulateParams {
  startDate: string
  endDate: string
  productCds?: string[]
  processOverrides?: Record<string, Record<string, Record<string, number>>>
  runCalendarItems?: ProcessRunCalendarItem[]
  includeForecastMonths?: boolean
  baseMonth?: string
}

export function getProcessRunDays(startDate: string, endDate: string) {
  return request.get<{ data: { configured: boolean; startDate: string; endDate: string; items: ProcessRunCalendarItem[] } }>(
    `${BASE}/process-run-days`,
    { params: { startDate, endDate } }
  )
}

export function putProcessRunDays(body: { startDate: string; endDate: string; items: ProcessRunCalendarItem[] }) {
  return request.put(`${BASE}/process-run-days`, body)
}

export function getFormingDailyPlanSummary(params: {
  startDate: string
  endDate: string
  productCd?: string
  includeForecastMonths?: boolean
  baseMonth?: string
  includeOrderMatrix?: boolean
}) {
  return request.get<{ code: number; data: FormingDailyPlanSummaryData }>(`${BASE}/summary`, { params })
}

export function getFormingOrderMatrix(params: { startDate: string; endDate: string; productCd?: string }) {
  return request.get<{ code: number; data: { rows: OrderMatrixRow[]; dates: string[] } }>(`${BASE}/order-matrix`, {
    params,
  })
}

export function getOrderForecast(params: { baseMonth: string; months?: number; productCd?: string }) {
  return request.get<{ code: number; data: { months: OrderForecastMonth[] } }>(`${BASE}/order-forecast`, { params })
}

export function simulateFormingDailyPlan(body: SimulateParams) {
  return request.post<{ code: number; data: FormingDailyPlanSummaryData }>(`${BASE}/simulate`, body)
}

export function listFormingPlanScenarios() {
  return request.get<{ code: number; data: { items: FormingPlanScenario[] } }>(`${BASE}/scenarios`)
}

export function createFormingPlanScenario(body: {
  name: string
  startDate: string
  endDate: string
  baseMonth: string
  includeForecastMonths?: boolean
  processOverrides?: Record<string, Record<string, Record<string, number>>>
  runCalendarItems?: ProcessRunCalendarItem[]
  notes?: string
}) {
  return request.post(`${BASE}/scenarios`, body)
}

export function getFormingPlanScenario(id: number) {
  return request.get<{ code: number; data: FormingPlanScenario & { payload: ScenarioPayload } }>(`${BASE}/scenarios/${id}`)
}

export function updateFormingPlanScenario(id: number, body: Partial<{
  name: string
  processOverrides: Record<string, Record<string, Record<string, number>>>
  runCalendarItems: ProcessRunCalendarItem[]
  includeForecastMonths: boolean
  notes: string
}>) {
  return request.put(`${BASE}/scenarios/${id}`, body)
}

export function simulateFormingPlanScenario(id: number) {
  return request.post<{ code: number; data: FormingDailyPlanSummaryData }>(`${BASE}/scenarios/${id}/simulate`)
}

export function applyFormingPlanScenario(id: number) {
  return request.post<{ code: number; data: { updated: number }; message: string }>(`${BASE}/scenarios/${id}/apply`)
}

export function deleteFormingPlanScenario(id: number) {
  return request.delete(`${BASE}/scenarios/${id}`)
}

/**
 * 生産検討会資料 API（/api/erp/production-review/*）
 */
import request from '@/shared/api/request'

const BASE = '/api/erp/production-review'

export interface ProductionReviewMonthItem {
  target_month: string
  status: string
  updated_at?: string | null
}

export interface CapacityRow {
  process_cd: string
  process_name: string
  equipment_label?: string
  standard_rate: number
  shift_label?: string
  working_days?: number
  daily_regular_hours: number
  sort_order?: number
}

export interface PerformanceRow {
  key: string
  name: string
  plan_th: number
  forecast_th: number
  actual_th: number
  vs_forecast_th: number
  vs_plan_th: number
  productivity_prev?: number | null
  productivity_curr?: number | null
  productivity_delta?: number | null
}

export interface LoadPlanRow {
  process_cd: string
  process_name: string
  plan_th: number
  daily_th: number
  equipment_label: string
  standard_rate: number
  shift_label: string
  regular_hours: number
  required_hours: number
  load_rate_pct: number
  daily_operation_hours: number
  working_days: number
  /** 月間最大生産量（千本）= 設備×能率×24H×稼働日×96% */
  max_monthly_th?: number
  /** 月計画 ÷ 月間最大 × 100 */
  plan_vs_max_monthly_pct?: number
}

export interface InventoryRow {
  key: string
  name: string
  prev_inventory_th: number
  prev_rate: number
  prev_rate_adj?: number
  prev_days?: number
  curr_inventory_th: number
  curr_rate: number
  curr_rate_adj?: number
  curr_days?: number
  delta_th: number
  /** 行ごとの工程内示（千本） */
  prev_forecast_th?: number
  curr_forecast_th?: number
  prev_forecast_adj_th?: number
  curr_forecast_adj_th?: number
  children?: InventoryRow[]
}

export interface InventorySection {
  inventory_month_label: string
  prev_forecast_label: string
  curr_forecast_label: string
  prev_forecast_th: number
  curr_forecast_th: number
  prev_forecast_adj_th?: number
  curr_forecast_adj_th?: number
  prev_forecast_year?: number
  prev_forecast_month?: number
  curr_forecast_year?: number
  curr_forecast_month?: number
  prev_workdays?: number
  curr_workdays?: number
  standard_workdays?: number
  product_target_rate?: number
  product_target_days?: number
  /** 工程別補正率目標（切断0.15 / 成型0.15 / メッキ0.19 / 溶接0.19 / 製品0.36） */
  process_target_rates?: Record<string, number>
  /** 工程別在庫日数目標（補正率×標準稼働日） */
  process_target_days?: Record<string, number>
  product_level?: 'danger' | 'ok' | 'high' | string
  /** 当月在庫の基準日（YYYY-MM-DD）。未設定時は月末在庫 */
  curr_inventory_as_of?: string | null
  rows: InventoryRow[]
  comments?: string[]
}

export interface WorkingDaysMonthItem {
  year: number
  month: number
  label: string
  working_days: number
  source?: 'saved' | 'estimated' | string
}

export interface ScrapMonthlyItem {
  year: number
  month: number
  rate_new_pct: number
  rate_old_pct: number
  loss_qty: number
  loss_th?: number
  /** @deprecated 互換用 */
  scrap_th?: number
  /** @deprecated 互換用（= rate_old_pct） */
  rate_pct?: number
}

export interface ScrapSection {
  monthly: ScrapMonthlyItem[]
  fiscal_year?: number
  fiscal_year_label?: string
  range_label?: string
  current_month_rate_new_pct?: number
  current_month_rate_old_pct?: number
  current_month_loss_qty?: number
  current_month_loss_th?: number
  avg_rate_new_current_fy_pct?: number
  avg_rate_old_current_fy_pct?: number
  avg_rate_new_prev_fy_pct?: number
  avg_rate_old_prev_fy_pct?: number
  avg_loss_current_fy_qty?: number
  avg_loss_prev_fy_qty?: number
  avg_loss_current_fy_th?: number
  avg_loss_prev_fy_th?: number
  improvement_rate_new_pt?: number
  improvement_rate_old_pt?: number
  improvement_loss_qty?: number
  /** @deprecated 互換用 */
  current_month_rate_pct?: number
  current_month_scrap_th?: number
  avg_rate_current_fy_pct?: number
  avg_rate_prev_fy_pct?: number
  avg_scrap_current_fy_th?: number
  avg_scrap_prev_fy_th?: number
  improvement_rate_pt?: number
  improvement_scrap_th?: number
  comments?: string[]
}

export interface ProductionReviewData {
  target_month: string
  meta: {
    meeting_date?: string
    meeting_month_label?: string
    title?: string
    subtitle?: string
    title_note?: string
  }
  part01: {
    title?: string
    subtitle?: string
    performance: { month_label: string; rows: PerformanceRow[]; comments?: string[] }
    scrap: ScrapSection
    inventory: InventorySection
  }
  part02: {
    title?: string
    subtitle?: string
    load_plan: {
      month_label: string
      working_days: number
      forecast_th: number
      daily_forecast_th: number
      rows: LoadPlanRow[]
      comments?: string[]
    }
    inventory_forecast: InventorySection
  }
  part03: {
    title?: string
    subtitle?: string
    load_plan: ProductionReviewData['part02']['load_plan']
  }
  generated_at?: string
}

export interface ProductionReviewRecord {
  id?: number
  target_month: string
  status: string
  data: ProductionReviewData
  generated_at?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export function fetchSavedMonths(): Promise<{ success: boolean; data: ProductionReviewMonthItem[] }> {
  return request.get(`${BASE}/months`) as unknown as Promise<{
    success: boolean
    data: ProductionReviewMonthItem[]
  }>
}

export function fetchMeeting(month: string): Promise<{
  success: boolean
  data: ProductionReviewRecord
  source: 'saved' | 'computed'
}> {
  return request.get(`${BASE}/${month}`) as unknown as Promise<{
    success: boolean
    data: ProductionReviewRecord
    source: 'saved' | 'computed'
  }>
}

export function recalculateMeeting(month: string): Promise<{ success: boolean; data: ProductionReviewData }> {
  return request.post(`${BASE}/${month}/recalculate`) as unknown as Promise<{
    success: boolean
    data: ProductionReviewData
  }>
}

export function saveMeeting(
  month: string,
  body: { status: string; data: ProductionReviewData },
): Promise<{ success: boolean; data: ProductionReviewRecord; message: string }> {
  return request.put(`${BASE}/${month}`, body) as unknown as Promise<{
    success: boolean
    data: ProductionReviewRecord
    message: string
  }>
}

export async function downloadMeetingPptx(month: string, data?: ProductionReviewData): Promise<void> {
  const resp = (await request.post(
    `${BASE}/${month}/pptx`,
    data ? { status: 'draft', data } : {},
    { responseType: 'blob' },
  )) as unknown as Blob
  const url = window.URL.createObjectURL(resp)
  const a = document.createElement('a')
  a.href = url
  a.download = `${month}生産検討会.pptx`
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

export function fetchCapacity(): Promise<{ success: boolean; data: CapacityRow[] }> {
  return request.get(`${BASE}/capacity`) as unknown as Promise<{ success: boolean; data: CapacityRow[] }>
}

export function saveCapacity(items: CapacityRow[]): Promise<{ success: boolean; data: CapacityRow[] }> {
  return request.put(`${BASE}/capacity`, { items }) as unknown as Promise<{
    success: boolean
    data: CapacityRow[]
  }>
}

export function fetchWorkingDays(year: number): Promise<{
  success: boolean
  data: { year: number; items: WorkingDaysMonthItem[] }
}> {
  return request.get(`${BASE}/working-days`, { params: { year } }) as unknown as Promise<{
    success: boolean
    data: { year: number; items: WorkingDaysMonthItem[] }
  }>
}

export function fetchInventoryByDate(date: string): Promise<{
  success: boolean
  data: {
    date: string
    date_label: string
    quantities_th: Record<string, number>
  }
}> {
  return request.get(`${BASE}/inventory-by-date`, { params: { date } }) as unknown as Promise<{
    success: boolean
    data: {
      date: string
      date_label: string
      quantities_th: Record<string, number>
    }
  }>
}

export type CommentGenerateKind =
  | 'performance'
  | 'scrap'
  | 'inventory'
  | 'inventory_forecast'
  | 'load_plan'

export function generateComments(
  kind: CommentGenerateKind,
  section: Record<string, unknown>,
): Promise<{ success: boolean; data: { kind: string; comments: string[] } }> {
  return request.post(`${BASE}/comments/generate`, { kind, section }) as unknown as Promise<{
    success: boolean
    data: { kind: string; comments: string[] }
  }>
}

export function saveWorkingDays(
  items: Array<{ year: number; month: number; working_days: number; remark?: string | null }>,
): Promise<{ success: boolean; data?: WorkingDaysMonthItem[]; message?: string }> {
  return request.put(`${BASE}/working-days`, { items }) as unknown as Promise<{
    success: boolean
    data?: WorkingDaysMonthItem[]
    message?: string
  }>
}

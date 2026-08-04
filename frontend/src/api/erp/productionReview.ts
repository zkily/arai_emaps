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
  /** 対象月 YYYY-MM。空=デフォルト */
  target_month?: string
  equipment_label?: string
  standard_rate: number
  shift_label?: string
  working_days?: number
  /** 稼働率(%) 定時H計算用。未設定時は 96 */
  utilization_rate_pct?: number
  /** 計画調整率(%)。表示計画 = 元計画 × 調整率 ÷ 100。未設定時は 100 */
  plan_adjust_rate_pct?: number
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
  /** 元計画(千本)。調整率適用前 */
  base_plan_th?: number
  /** 計画調整率(%) */
  plan_adjust_rate_pct?: number
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
  /** 稼働率(%) 定時H計算用 */
  utilization_rate_pct?: number
  /** 月の暦日数（設備稼働率の分母用） */
  calendar_days?: number
  /** 設備稼働率(%) = 所要H ÷ (設備数×暦日×24H)×100。検査は null */
  equipment_utilization_pct?: number | null
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
  /** 前月在庫の基準日（YYYY-MM-DD）。在庫予測テーブル用。未設定時は前月末在庫 */
  prev_inventory_as_of?: string | null
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
      month?: string
      working_days: number
      calendar_days?: number
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
    /** 旧保存データには無い場合あり。再計算で生成 */
    inventory_forecast?: InventorySection
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

export function deleteMeeting(month: string): Promise<{ success: boolean; message: string }> {
  return request.delete(`${BASE}/${month}`) as unknown as Promise<{
    success: boolean
    message: string
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

export async function downloadScrapPptx(
  month: string,
  body: {
    scrap: Record<string, unknown>
    chart_image_base64?: string | null
    meeting_label?: string
  },
): Promise<void> {
  const resp = (await request.post(`${BASE}/${month}/pptx/scrap`, body, {
    responseType: 'blob',
  })) as unknown as Blob
  const url = window.URL.createObjectURL(resp)
  const a = document.createElement('a')
  a.href = url
  a.download = `${month}廃棄率及び廃棄本数.pptx`
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

export function fetchCapacity(month?: string): Promise<{
  success: boolean
  data: CapacityRow[]
  source?: 'monthly' | 'default' | string
  target_month?: string
}> {
  return request.get(`${BASE}/capacity`, {
    params: month ? { month } : undefined,
  }) as unknown as Promise<{
    success: boolean
    data: CapacityRow[]
    source?: 'monthly' | 'default' | string
    target_month?: string
  }>
}

export function saveCapacity(
  items: CapacityRow[],
  month?: string,
): Promise<{ success: boolean; data: CapacityRow[]; message?: string; target_month?: string }> {
  return request.put(`${BASE}/capacity`, { items }, {
    params: month ? { month } : undefined,
  }) as unknown as Promise<{
    success: boolean
    data: CapacityRow[]
    message?: string
    target_month?: string
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

export interface EfficiencyTrendSeries {
  process_cd: string
  process_name: string
  values: Array<number | null>
}

export interface EfficiencyTrendData {
  start_month: string
  end_month: string
  months: string[]
  month_labels: string[]
  processes: Array<{ process_cd: string; process_name: string }>
  series: EfficiencyTrendSeries[]
}

export function fetchEfficiencyTrend(params: {
  start_month: string
  end_month: string
  processes?: string[]
}): Promise<{ success: boolean; data: EfficiencyTrendData }> {
  return request.get(`${BASE}/efficiency-trend`, {
    params: {
      start_month: params.start_month,
      end_month: params.end_month,
      processes: params.processes?.length ? params.processes.join(',') : undefined,
    },
  }) as unknown as Promise<{ success: boolean; data: EfficiencyTrendData }>
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

/**
 * 予算管理 API（見直し予算 CSV 取込・分析）
 */
import request from '@/utils/request'

const BASE = '/api/budget'

export interface BudgetMonthKey {
  year: number
  month: number
}

export interface BudgetMonthlyItem {
  id: number
  year: number
  month: number
  development_code?: string | null
  part_number: string
  product_cd?: string | null
  product_name?: string | null
  budget_qty: number
  match_status: string
  import_batch_id?: number | null
  source_file_name?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface BudgetSummary {
  year?: number | null
  month?: number | null
  product_count: number
  matched_count: number
  unmatched_count: number
  total_budget_qty: number
  month_count: number
}

export interface BudgetUploadResult {
  success: boolean
  batch_id: number
  file_name: string
  months: BudgetMonthKey[]
  total_rows: number
  matched_rows: number
  unmatched_rows: number
  inserted_rows: number
  updated_rows: number
  unmatched_samples: Array<{
    line_no: number
    development_code?: string
    part_number: string
  }>
  message: string
}

export interface BudgetImportBatch {
  id: number
  file_name: string
  months_json?: string | null
  total_rows: number
  matched_rows: number
  unmatched_rows: number
  inserted_rows: number
  updated_rows: number
  uploaded_by?: string | null
  remark?: string | null
  created_at?: string | null
}

export interface ProcessLoadItem {
  process_cd: string
  process_name: string
  product_count: number
  total_budget_qty: number
  total_hours: number
  is_outsource: number
}

export interface EquipmentLoadItem {
  machine_cd: string
  machine_name: string
  product_count: number
  total_budget_qty: number
  total_hours: number
  avg_efficiency_rate?: number | null
}

export interface CostAnalysisItem {
  product_cd?: string | null
  product_name?: string | null
  part_number: string
  development_code?: string | null
  budget_qty: number
  unit_price?: number | null
  unit_cost_std?: number | null
  sales_amount: number
  cost_amount: number
  margin_amount: number
}

export interface CostAnalysisResult {
  version_id?: number | null
  items: CostAnalysisItem[]
  totals: {
    budget_qty: number
    sales_amount: number
    cost_amount: number
    margin_amount: number
  }
}

export interface TrendItem {
  year: number
  month: number
  label: string
  product_count: number
  total_budget_qty: number
  matched_count: number
  working_days?: number
  avg_daily_qty?: number | null
}

export interface ProcessTrendMonth {
  year: number
  month: number
  label: string
  working_days?: number
}

export interface ProcessTrendSeries {
  process_cd: string
  process_name: string
  is_outsource: number
  series: number[]
  avg_daily_series?: Array<number | null>
  working_days_series?: number[]
  working_days_override_series?: boolean[]
  total_qty: number
}

export interface ProcessTrendResult {
  months: ProcessTrendMonth[]
  processes: ProcessTrendSeries[]
}

export interface WorkingDaysItem {
  year: number
  month: number
  label: string
  working_days: number
  total_budget_qty: number
  avg_daily_qty?: number | null
}

export interface ProcessWorkingDaysOption {
  process_cd: string
  process_name: string
}

export interface ProcessWorkingDaysOverride {
  year: number
  month: number
  label: string
  process_cd: string
  process_name: string
  working_days: number
}

export interface WorkingDaysBundle {
  defaults: WorkingDaysItem[]
  process_options: ProcessWorkingDaysOption[]
  process_overrides: ProcessWorkingDaysOverride[]
}

function unwrapData<T>(res: any): T {
  if (res?.data !== undefined && res?.success !== undefined) return res.data as T
  return res as T
}

export function fetchBudgetMonths(): Promise<BudgetMonthKey[]> {
  return request.get(`${BASE}/months`).then((res: any) => unwrapData(res) ?? [])
}

export function fetchBudgetSummary(params?: {
  year?: number
  month?: number
}): Promise<BudgetSummary> {
  return request.get(`${BASE}/summary`, { params }).then((res: any) => unwrapData(res) ?? {})
}

export function fetchBudgetList(params?: {
  year?: number
  month?: number
  keyword?: string
  match_status?: string
  page?: number
  page_size?: number
}): Promise<{ total: number; page: number; page_size: number; items: BudgetMonthlyItem[] }> {
  return request.get(`${BASE}/list`, { params }).then((res: any) => unwrapData(res) ?? { total: 0, page: 1, page_size: 50, items: [] })
}

export function fetchBudgetImports(limit = 20): Promise<BudgetImportBatch[]> {
  return request.get(`${BASE}/imports`, { params: { limit } }).then((res: any) => unwrapData(res) ?? [])
}

export function uploadBudgetCsv(file: File): Promise<BudgetUploadResult> {
  const form = new FormData()
  form.append('file', file)
  return request.post(`${BASE}/upload`, form, { timeout: 120000 }) as Promise<BudgetUploadResult>
}

export function fetchBudgetTrend(year?: number): Promise<TrendItem[]> {
  return request
    .get(`${BASE}/analysis/trend`, { params: year ? { year } : {} })
    .then((res: any) => unwrapData(res) ?? [])
}

export function fetchProcessTrend(year?: number): Promise<ProcessTrendResult> {
  return request
    .get(`${BASE}/analysis/process-trend`, { params: year ? { year } : {} })
    .then(
      (res: any) =>
        unwrapData(res) ?? {
          months: [],
          processes: [],
        },
    )
}

export function fetchWorkingDays(year?: number): Promise<WorkingDaysBundle> {
  return request
    .get(`${BASE}/working-days`, { params: year ? { year } : {} })
    .then((res: any) => {
      const data = unwrapData(res)
      // 後方互換：配列のみ返る場合
      if (Array.isArray(data)) {
        return {
          defaults: data as WorkingDaysItem[],
          process_options: [],
          process_overrides: [],
        }
      }
      return (
        data ?? {
          defaults: [],
          process_options: [],
          process_overrides: [],
        }
      )
    })
}

export function saveWorkingDays(
  items: Array<{ year: number; month: number; working_days: number; remark?: string | null }>,
): Promise<{ success?: boolean; data?: WorkingDaysItem[]; message?: string }> {
  return request.put(`${BASE}/working-days`, { items }) as Promise<{
    success?: boolean
    data?: WorkingDaysItem[]
    message?: string
  }>
}

export function saveProcessWorkingDays(
  items: Array<{
    year: number
    month: number
    process_cd: string
    process_name?: string | null
    working_days: number | null
    remark?: string | null
  }>,
): Promise<{ success?: boolean; data?: WorkingDaysBundle; message?: string }> {
  return request.put(`${BASE}/working-days/process`, { items }) as Promise<{
    success?: boolean
    data?: WorkingDaysBundle
    message?: string
  }>
}

export function fetchProcessLoad(year: number, month: number): Promise<ProcessLoadItem[]> {
  return request
    .get(`${BASE}/analysis/process`, { params: { year, month } })
    .then((res: any) => unwrapData(res) ?? [])
}

export function fetchEquipmentLoad(year: number, month: number): Promise<EquipmentLoadItem[]> {
  return request
    .get(`${BASE}/analysis/equipment`, { params: { year, month } })
    .then((res: any) => unwrapData(res) ?? [])
}

export function fetchCostAnalysis(year: number, month: number): Promise<CostAnalysisResult> {
  return request
    .get(`${BASE}/analysis/cost`, { params: { year, month } })
    .then((res: any) => unwrapData(res) ?? { items: [], totals: { budget_qty: 0, sales_amount: 0, cost_amount: 0, margin_amount: 0 } })
}

export function deleteBudgetMonth(year: number, month: number): Promise<{ deleted: number; message: string }> {
  return request.delete(`${BASE}/month`, { params: { year, month } }) as Promise<{ deleted: number; message: string }>
}

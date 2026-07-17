/**
 * 在庫報告（四半期・半期・年間）API
 */
import request from '@/shared/api/request'

export interface QuarterOption {
  fiscal_year: number
  quarter: number
  label: string
  is_current: boolean
}

export interface InventorySeriesPoint {
  month: string
  month_label: string
  wip_qty: number
  product_qty: number
  total_qty: number
}

export interface ScrapSeriesPoint {
  month: string
  month_label: string
  rate_percent: number | null
  defect_rate_percent?: number | null
  /** 不良＋廃棄の全工程連乗ロス率（品質ロス率） */
  quality_loss_rate_percent?: number | null
  sum_defect: number
  sum_scrap: number
  sum_defect_and_scrap: number
  rate_basis?: string
  processes?: Array<{
    key: string
    label: string
    sum_actual: number
    sum_defect: number
    sum_scrap: number
    sum_defect_and_scrap: number
    rate_percent: number | null
  }>
}

export interface DiffMonthProcessRow {
  month: string
  month_label: string
  process_cd: string
  process_name: string
  theoretical_qty: number
  stocktake_qty: number
  diff_qty: number
  diff_rate: number | null
  match_rate: number
}

export interface ReportHighlight {
  type: string
  tone: string
  title: string
  text: string
}

export interface MonthlyReportKpi {
  month: string
  month_label: string
  closing_wip_qty: number
  closing_product_qty: number
  closing_total_qty: number
  scrap_rate_percent: number | null
  defect_rate_percent: number | null
  defect_qty: number
  scrap_qty: number
  match_rate: number
  diff_abs: number
  bulk_disposal_count: number
  bulk_disposal_quantity: number
  bulk_disposal_pending: number
}

export interface QuarterlyReportPayload {
  fiscal_year: number
  /** 1-4=Q1-Q4, 5=上期, 6=下期, 7=年間 */
  quarter: number
  period_code?: number
  report_type?: 'quarter' | 'half' | 'annual'
  label: string
  period: { start: string; end: string }
  generated_at: string
  kpi: {
    closing_wip_qty: number
    closing_product_qty: number
    closing_total_qty: number
    avg_scrap_rate_percent: number | null
    total_defect_qty: number
    total_scrap_qty: number
    avg_match_rate: number
    total_diff_abs: number
    bulk_disposal_count: number
    bulk_disposal_pending: number
  }
  monthly_kpis: MonthlyReportKpi[]
  inventory_series: InventorySeriesPoint[]
  scrap_series: ScrapSeriesPoint[]
  diff_by_month_process: DiffMonthProcessRow[]
  top_mismatch: Array<Record<string, unknown>>
  bulk_disposal: {
    count: number
    total_quantity: number
    pending_count: number
    by_category: Array<{ category: string; count: number; quantity: number }>
    by_month: Array<{
      month: string
      count: number
      quantity: number
      pending_count: number
    }>
    items: Array<Record<string, unknown>>
  }
  previous_quarter: {
    fiscal_year: number
    quarter: number
    label: string
    closing_total_qty: number
    closing_wip_qty: number
    closing_product_qty: number
    delta_total_qty: number
    delta_wip_qty: number
    delta_product_qty: number
  } | null
  previous_period?: {
    fiscal_year: number
    quarter: number
    label: string
    closing_total_qty: number
    closing_wip_qty: number
    closing_product_qty: number
    delta_total_qty: number
    delta_wip_qty: number
    delta_product_qty: number
  } | null
  months: Array<Record<string, unknown>>
  highlights: ReportHighlight[]
}

export interface ScrapOverrideMonth {
  rate_percent: number | null
  sum_defect?: number | null
  sum_scrap?: number | null
  note?: string
}

export type ScrapOverrides = Record<string, ScrapOverrideMonth>

export interface SavedReportSummary {
  id: number
  fiscal_year: number
  quarter: number
  title: string
  status: string
  label: string
  generated_at: string | null
  updated_at: string | null
}

export interface SavedReportDetail {
  id: number
  fiscal_year: number
  quarter: number
  title: string
  status: string
  payload: QuarterlyReportPayload
  scrap_overrides: ScrapOverrides
  executive_summary: string | null
  action_items: string | null
  notes: string | null
  generated_at: string | null
  created_at: string | null
  updated_at: string | null
}

function unwrap<T>(res: unknown): T {
  const r = res as { success?: boolean; data?: T }
  return (r?.data ?? res) as T
}

export const inventoryReportApi = {
  async getQuarterOptions() {
    const res = await request.get('/api/erp/inventory-report/quarters')
    return unwrap<{
      current_fiscal_year: number
      current_quarter: number
      options: QuarterOption[]
    }>(res)
  },

  async generate(fiscalYear: number, quarter: number) {
    const res = await request.get('/api/erp/inventory-report/generate', {
      params: { fiscal_year: fiscalYear, quarter },
    })
    return unwrap<QuarterlyReportPayload>(res)
  },

  async listSaved(fiscalYear?: number) {
    const res = await request.get('/api/erp/inventory-report/saved', {
      params: fiscalYear != null ? { fiscal_year: fiscalYear } : undefined,
    })
    return unwrap<{ list: SavedReportSummary[] }>(res)
  },

  async getSaved(id: number) {
    const res = await request.get(`/api/erp/inventory-report/saved/${id}`)
    return unwrap<SavedReportDetail>(res)
  },

  async save(body: {
    fiscal_year: number
    quarter: number
    title?: string
    status?: 'draft' | 'final'
    payload?: QuarterlyReportPayload
    scrap_overrides?: ScrapOverrides
    executive_summary?: string
    action_items?: string
    notes?: string
    regenerate?: boolean
  }) {
    const res = await request.post('/api/erp/inventory-report/saved', body)
    return unwrap<SavedReportDetail>(res)
  },

  async remove(id: number) {
    const res = await request.delete(`/api/erp/inventory-report/saved/${id}`)
    return unwrap<{ id: number }>(res)
  },
}

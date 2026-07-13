/**
 * ラベル枚数管理 API（複数月ロール対応）
 */
import request from '@/shared/api/request'

const BASE = '/api/master/label-quantity'

export type LabelQuantityType = 'molding' | 'product_use'

export interface LabelQuantityKpi {
  total: number
  sufficient: number
  insufficient: number
  unit_qty_missing: number
  shortage_qty_sum: number
  issue_qty_sum: number
  issued_qty_sum?: number
  opening_stock_sum: number
  required_qty_sum: number
  demand_units_sum: number
  closing_theory_sum?: number
}

export interface LabelQuantityMonthSnap {
  id?: number | null
  year_month: string
  demand_units: number
  required_qty?: number | null
  opening_stock: number
  opening_locked?: boolean
  shortage_qty: number
  issue_qty: number
  /** 発行済枚数（印刷実績累計） */
  issued_qty?: number
  suggested_issue_sheets?: number
  issue_labels?: number
  closing_theory?: number | null
  is_sufficient: boolean
  unit_qty_missing?: boolean
  labels_per_sheet?: number
  is_saved?: boolean
}

export interface LabelQuantityRow {
  product_cd: string
  label_product_name?: string | null
  master_product_name?: string | null
  supply_type?: string | null
  unit_qty?: number | null
  unit_qty_missing?: boolean
  last_issue_history?: string | null
  labels_per_sheet?: number
  safety_factor?: number
  months: LabelQuantityMonthSnap[]
  // flat compat (first month)
  year_month?: string
  demand_units?: number
  required_qty?: number | null
  opening_stock?: number
  opening_locked?: boolean
  shortage_qty?: number
  issue_qty?: number
  issued_qty?: number
  closing_theory?: number | null
  is_sufficient?: boolean
}

export interface LabelQuantityListResponse {
  success?: boolean
  start_month?: string
  months_count?: number
  month_keys?: string[]
  list: LabelQuantityRow[]
  products?: LabelQuantityRow[]
  kpi: LabelQuantityKpi
  safety_factor?: number
  labels_per_sheet?: number
  message?: string
  saved?: number
  created?: number
  updated?: number
  rolled_openings?: number
  issue_updated?: number
}

export interface LabelQuantityQuery {
  start_month: string
  months?: number
  label_type: LabelQuantityType
  keyword?: string
  sufficiency?: string
  supply_type?: string
}

export interface LabelQuantitySaveItem {
  product_cd: string
  year_month: string
  opening_stock: number
  issue_qty: number
  issued_qty?: number
  opening_locked?: boolean
  last_issue_history?: string | null
}

export function fetchLabelQuantityList(params: LabelQuantityQuery) {
  return request.get<LabelQuantityListResponse>(BASE, { params })
}

export function saveLabelQuantityBatch(body: {
  label_type: LabelQuantityType
  start_month: string
  months: number
  items: LabelQuantitySaveItem[]
}) {
  return request.put<LabelQuantityListResponse>(`${BASE}/batch`, body)
}

export function fillLabelQuantityIssueQty(body: {
  start_month: string
  months: number
  label_type: LabelQuantityType
  only_unsaved?: boolean
}) {
  return request.post<LabelQuantityListResponse>(`${BASE}/fill-issue-qty`, body)
}

export function recalculateLabelQuantity(body: {
  start_month: string
  months: number
  label_type: LabelQuantityType
  fill_issue_qty?: boolean
}) {
  return request.post<LabelQuantityListResponse>(`${BASE}/recalculate`, body)
}

export interface LabelQuantityPrintRecordItem {
  product_cd: string
  paper_sheets: number
  labels_per_sheet?: number
  label_count?: number
}

/** 成型用/製品用ラベル印刷後に最終発行・印刷履歴を反映 */
export function recordLabelQuantityPrint(body: {
  label_type: LabelQuantityType
  year_month?: string
  items: LabelQuantityPrintRecordItem[]
}) {
  return request.post<{
    success?: boolean
    message?: string
    year_month?: string
    created?: number
    updated?: number
    items?: Array<{ product_cd: string; last_issue_history?: string }>
  }>(`${BASE}/record-print`, body)
}

/** 月末理論残 = 月初 + 発行済 − 必要枚数 */
export function calcClosingTheory(
  opening: number,
  issuedQty: number,
  required: number | null | undefined
): number | null {
  if (required == null) return null
  return Number(opening || 0) + Math.max(0, Number(issuedQty) || 0) - Number(required)
}

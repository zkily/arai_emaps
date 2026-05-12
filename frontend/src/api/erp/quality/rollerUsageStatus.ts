/**
 * ローラー使用状況 API（roller_usage_status）
 */
import request from '@/shared/api/request'

export interface RollerUsageStatusRow {
  id?: number
  roller_cd?: string
  roller_type?: string | null
  machine_cd?: string | null
  machine_name?: string | null
  exchange_freq_qty?: number | null
  exchange_freq_month?: number | null
  cleaning_freq_month?: number | null
  exec_type?: string | null
  last_exec_date?: string | null
  next_exec_date?: string | null
  prod_cumulative_qty?: number | null
  /** 前月末までの生産累計（再計算で自動更新） */
  prod_cumulative_qty_prev_month_end?: number | null
  /** 手入力補正（自動累計に加算・マイナス可） */
  prod_manual_addon_qty?: number | null
  planned_product_cd?: string | null
  exchange_remaining_qty?: number | null
  source_roller_master_updated_at?: string | null
  created_at?: string
  updated_at?: string
}

export interface RollerUsageStatusListResponse {
  success?: boolean
  data?: { list: RollerUsageStatusRow[]; total: number }
  list?: RollerUsageStatusRow[]
  total?: number
}

export interface RollerUsageStatusListParams {
  keyword?: string
  machine_cd?: string
  exec_type?: string
  /** 並び替え列（API ホワイトリストと一致） */
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  page?: number
  pageSize?: number
}

const BASE = '/api/master/roller-usage-status'
const ACTION_BASE = '/api/master/roller-usage'

export function fetchRollerUsageStatusList(
  params?: RollerUsageStatusListParams,
): Promise<RollerUsageStatusListResponse> {
  return request.get(BASE, {
    params: {
      page: params?.page ?? 1,
      pageSize: params?.pageSize ?? 5000,
      ...(params?.keyword ? { keyword: params.keyword } : {}),
      ...(params?.machine_cd ? { machine_cd: params.machine_cd } : {}),
      ...(params?.exec_type ? { exec_type: params.exec_type } : {}),
      ...(params?.sortBy && params?.sortOrder
        ? { sortBy: params.sortBy, sortOrder: params.sortOrder }
        : {}),
    },
  }) as Promise<RollerUsageStatusListResponse>
}

export function updateRollerUsageStatus(
  id: number,
  data: Partial<RollerUsageStatusRow>,
): Promise<{ success: boolean; data: RollerUsageStatusRow }> {
  return request.put(`${BASE}/${id}`, data) as Promise<{ success: boolean; data: RollerUsageStatusRow }>
}

export function syncFromRollerMaster(): Promise<{
  success: boolean
  inserted: number
  updated: number
  message: string
}> {
  return request.post(`${ACTION_BASE}/sync-from-master`, {}) as Promise<{
    success: boolean
    inserted: number
    updated: number
    message: string
  }>
}

export function recalculatePredictions(roller_cds?: string[]): Promise<{
  success: boolean
  recalculated: number
  message: string
}> {
  return request.post(`${ACTION_BASE}/recalculate`, roller_cds ? { roller_cds } : {}) as Promise<{
    success: boolean
    recalculated: number
    message: string
  }>
}

/**
 * ローラー予定スケジュール API（roller_usage_plan）
 */
import request from '@/shared/api/request'

export interface RollerUsagePlanRow {
  id?: number
  roller_cd?: string
  plan_month?: string
  planned_exec_date?: string
  planned_product_cd?: string | null
  exec_type?: string
  status?: 'planned' | 'done' | 'cancelled'
  sort_order?: number
  note?: string | null
  created_by?: string | null
  created_at?: string
  updated_at?: string
}

export interface RollerUsagePlanListResponse {
  success?: boolean
  data?: { list: RollerUsagePlanRow[]; total: number }
  list?: RollerUsagePlanRow[]
  total?: number
}

const BASE = '/api/master/roller-usage-plan'

export function fetchRollerUsagePlanList(params?: {
  roller_cd?: string
  planMonth?: string
  status?: string
  fromDate?: string
  page?: number
  pageSize?: number
}): Promise<RollerUsagePlanListResponse> {
  return request.get(BASE, {
    params: {
      page: params?.page ?? 1,
      pageSize: params?.pageSize ?? 500,
      ...(params?.roller_cd ? { roller_cd: params.roller_cd } : {}),
      ...(params?.planMonth ? { planMonth: params.planMonth } : {}),
      ...(params?.status ? { status: params.status } : {}),
      ...(params?.fromDate ? { fromDate: params.fromDate } : {}),
    },
  }) as Promise<RollerUsagePlanListResponse>
}

export function createRollerUsagePlan(
  data: Partial<RollerUsagePlanRow>,
): Promise<{ success: boolean; data: RollerUsagePlanRow }> {
  return request.post(BASE, data) as Promise<{ success: boolean; data: RollerUsagePlanRow }>
}

export function batchSyncRollerUsagePlan(body: {
  roller_cd: string
  plan_month: string
  items: Array<{
    planned_exec_date: string
    planned_product_cd?: string | null
    exec_type?: string
    sort_order?: number
    note?: string | null
  }>
}): Promise<{ success: boolean; created: number; message: string }> {
  return request.post(`${BASE}/batch-sync`, body) as Promise<{
    success: boolean
    created: number
    message: string
  }>
}

export function updateRollerUsagePlan(
  id: number,
  data: Partial<RollerUsagePlanRow>,
): Promise<{ success: boolean; data: RollerUsagePlanRow }> {
  return request.put(`${BASE}/${id}`, data) as Promise<{ success: boolean; data: RollerUsagePlanRow }>
}

export function deleteRollerUsagePlan(id: number): Promise<{ success: boolean; message: string }> {
  return request.delete(`${BASE}/${id}`) as Promise<{ success: boolean; message: string }>
}

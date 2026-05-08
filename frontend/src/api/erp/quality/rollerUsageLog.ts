/**
 * ローラー使用ログ API（roller_usage_log）
 */
import request from '@/shared/api/request'

export interface RollerUsageLogRow {
  id?: number
  roller_cd?: string
  exec_type?: string
  exec_date?: string
  management_cd?: string | null
  note?: string | null
  created_by?: string | null
  created_at?: string
}

export interface RollerUsageLogListResponse {
  success?: boolean
  data?: { list: RollerUsageLogRow[]; total: number }
  list?: RollerUsageLogRow[]
  total?: number
}

const BASE = '/api/master/roller-usage-log'

export function fetchRollerUsageLogList(params?: {
  roller_cd?: string
  page?: number
  pageSize?: number
}): Promise<RollerUsageLogListResponse> {
  return request.get(BASE, {
    params: {
      page: params?.page ?? 1,
      pageSize: params?.pageSize ?? 200,
      ...(params?.roller_cd ? { roller_cd: params.roller_cd } : {}),
    },
  }) as Promise<RollerUsageLogListResponse>
}

export function createRollerUsageLog(
  data: Partial<RollerUsageLogRow>,
): Promise<{ success: boolean; data: RollerUsageLogRow }> {
  return request.post(BASE, data) as Promise<{ success: boolean; data: RollerUsageLogRow }>
}

export function deleteRollerUsageLog(id: number): Promise<{ success: boolean; message: string }> {
  return request.delete(`${BASE}/${id}`) as Promise<{ success: boolean; message: string }>
}

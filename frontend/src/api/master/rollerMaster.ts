/**
 * ローラーマスタ API（roller_master）
 */
import request from '@/shared/api/request'

export interface RollerMasterRow {
  id?: number
  roller_cd?: string
  roller_name?: string | null
  exchange_freq_qty?: number | null
  exchange_freq_month?: number | null
  cleaning_freq_month?: number | null
  category?: string | null
  note?: string | null
  machine_cd?: string | null
  created_at?: string
  updated_at?: string
}

export interface RollerMasterListResponse {
  success?: boolean
  data?: { list: RollerMasterRow[]; total: number }
  list?: RollerMasterRow[]
  total?: number
}

const BASE = '/api/master/roller-master'

export interface RollerMasterListParams {
  keyword?: string
  machine_cd?: string
  category?: string
  page?: number
  pageSize?: number
}

export function fetchRollerMasterList(
  params?: RollerMasterListParams
): Promise<RollerMasterListResponse> {
  const page = params?.page ?? 1
  const pageSize = params?.pageSize ?? 5000
  return request.get(BASE, {
    params: {
      page,
      pageSize,
      ...(params?.keyword ? { keyword: params.keyword } : {}),
      ...(params?.machine_cd ? { machine_cd: params.machine_cd } : {}),
      ...(params?.category ? { category: params.category } : {}),
    },
  }) as Promise<RollerMasterListResponse>
}

export function getRollerMasterById(id: number): Promise<RollerMasterRow> {
  return request.get(`${BASE}/${id}`) as Promise<RollerMasterRow>
}

export interface NextRollerCdResponse {
  success?: boolean
  roller_cd?: string
}

/** 新規登録用: A001 形式の次の roller_cd（サーバー側で最大値+1） */
export function fetchNextRollerCd(): Promise<NextRollerCdResponse> {
  return request.get(`${BASE}/next-roller-cd`) as Promise<NextRollerCdResponse>
}

export function createRollerMaster(data: Partial<RollerMasterRow>): Promise<RollerMasterRow> {
  return request.post(BASE, data) as Promise<RollerMasterRow>
}

export function updateRollerMaster(
  id: number,
  data: Partial<RollerMasterRow>
): Promise<RollerMasterRow> {
  return request.put(`${BASE}/${id}`, data) as Promise<RollerMasterRow>
}

export function deleteRollerMaster(id: number): Promise<{ message: string }> {
  return request.delete(`${BASE}/${id}`) as Promise<{ message: string }>
}

export function batchDeleteRollerMaster(
  ids: number[]
): Promise<{ message: string; deleted: number }> {
  return request.post(`${BASE}/batch-delete`, { ids }) as Promise<{ message: string; deleted: number }>
}

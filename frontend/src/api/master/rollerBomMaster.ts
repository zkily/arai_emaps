/**
 * ローラーBOM API（roller_bom）
 */
import request from '@/shared/api/request'

export interface RollerBomRow {
  id?: number
  roller_cd?: string
  roller_type?: string | null
  product_cd?: string
  machine_cd?: string
  created_at?: string
  updated_at?: string
}

export interface RollerBomListParams {
  keyword?: string
  machine_cd?: string
  product_cd?: string
  page?: number
  pageSize?: number
}

export interface RollerBomListResponse {
  success?: boolean
  data?: {
    list: RollerBomRow[]
    total: number
    roller_distinct_count?: number
    product_distinct_count?: number
    machine_distinct_count?: number
  }
  list?: RollerBomRow[]
  total?: number
  roller_distinct_count?: number
  product_distinct_count?: number
  machine_distinct_count?: number
}

const BASE = '/api/master/roller-bom'

export function fetchRollerBomList(params?: RollerBomListParams): Promise<RollerBomListResponse> {
  return request.get(BASE, { params }) as Promise<RollerBomListResponse>
}

export function getRollerBomById(id: number): Promise<RollerBomRow> {
  return request.get(`${BASE}/${id}`) as Promise<RollerBomRow>
}

export function createRollerBom(data: Partial<RollerBomRow>): Promise<RollerBomRow> {
  return request.post(BASE, data) as Promise<RollerBomRow>
}

export function updateRollerBom(id: number, data: Partial<RollerBomRow>): Promise<RollerBomRow> {
  return request.put(`${BASE}/${id}`, data) as Promise<RollerBomRow>
}

export function deleteRollerBom(id: number): Promise<{ message: string }> {
  return request.delete(`${BASE}/${id}`) as Promise<{ message: string }>
}

export function batchDeleteRollerBom(ids: number[]): Promise<{ message: string; deleted: number }> {
  return request.post(`${BASE}/batch-delete`, { ids }) as Promise<{ message: string; deleted: number }>
}

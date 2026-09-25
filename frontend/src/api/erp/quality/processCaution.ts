/**
 * 生産注意事項 API（品質管理 > 製品関連）
 * 工程別に製品生産時の注意事項を管理する。
 */
import request from '@/shared/api/request'

const BASE = '/api/quality/process-cautions'

export type ProcessCautionCode =
  | 'cutting'
  | 'chamfering'
  | 'forming'
  | 'welding'
  | 'plating'
  | 'inspection'

export type CautionScope = 'all' | 'product' | 'common'

export interface ProcessCaution {
  id: number
  process_code: ProcessCautionCode
  product_cd: string | null
  product_name: string | null
  caution_text: string
  is_active: boolean
  sort_order: number
  created_by: string | null
  updated_by: string | null
  created_at: string | null
  updated_at: string | null
}

export interface ProcessCautionPayload {
  process_code: ProcessCautionCode
  product_cd?: string | null
  product_name?: string | null
  caution_text: string
  is_active?: boolean
  sort_order?: number
}

interface ListResponse {
  success?: boolean
  data?: {
    list?: ProcessCaution[]
    total?: number
    active_count?: number
    inactive_count?: number
  }
  message?: string
}

export function fetchProcessCautions(params: {
  process_code?: string
  keyword?: string
  include_inactive?: boolean
  scope?: CautionScope | string
} = {}) {
  return request.get(BASE, { params }) as Promise<ListResponse>
}

export function lookupProcessCautions(params: {
  process_code: ProcessCautionCode | string
  product_cd?: string | null
}) {
  return request.get(`${BASE}/lookup`, { params }) as Promise<ListResponse>
}

export function createProcessCaution(data: ProcessCautionPayload) {
  return request.post(BASE, data) as Promise<{ success?: boolean; message?: string; data?: { id?: number } }>
}

export function updateProcessCaution(id: number, data: ProcessCautionPayload) {
  return request.put(`${BASE}/${id}`, data) as Promise<{ success?: boolean; message?: string }>
}

export function setProcessCautionActive(id: number, is_active: boolean) {
  return request.patch(`${BASE}/${id}/active`, { is_active }) as Promise<{ success?: boolean; message?: string }>
}

export function deleteProcessCaution(id: number) {
  return request.delete(`${BASE}/${id}`) as Promise<{ success?: boolean; message?: string }>
}

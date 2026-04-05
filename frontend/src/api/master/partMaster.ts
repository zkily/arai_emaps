/**
 * 部品マスタ API（標準単価・通貨・為替→standard_price_jpy）
 */
import request from '@/shared/api/request'

export interface PartMasterRow {
  id: number
  part_cd: string
  part_name: string
  uom: string
  unit_price: number
  currency: string
  exchange_rate: number
  standard_price_jpy: number
  supplier_cd?: string | null
  supplier_name?: string | null
  status: string
  remarks?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface PartMasterPayload {
  part_cd: string
  part_name: string
  uom?: string
  unit_price?: number
  currency?: string
  exchange_rate?: number
  supplier_cd?: string | null
  status?: string
  remarks?: string | null
}

export function getPartList(params: {
  keyword?: string
  status?: string
  page?: number
  pageSize?: number
}) {
  return request.get('/api/master/parts', { params }) as Promise<{
    success: boolean
    data: { list: PartMasterRow[]; total: number }
  }>
}

export function getPart(id: number) {
  return request.get(`/api/master/parts/${id}`) as Promise<{ success: boolean; data: PartMasterRow }>
}

export function createPart(data: PartMasterPayload) {
  return request.post('/api/master/parts', data) as Promise<{ success: boolean; data: PartMasterRow }>
}

export function updatePart(id: number, data: Partial<PartMasterPayload>) {
  return request.put(`/api/master/parts/${id}`, data) as Promise<{ success: boolean; data: PartMasterRow }>
}

export function deletePart(id: number) {
  return request.delete(`/api/master/parts/${id}`) as Promise<{ success: boolean; message?: string }>
}

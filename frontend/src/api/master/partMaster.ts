/**
 * 部品マスタ API（原通貨の単価・材料単価・為替）
 * standard_price_jpy＝総単価（円）＝単価×為替(>0)＋部品材料単価（原通貨をそのまま加算）
 */
import request from '@/shared/api/request'

export type PartKind = 'T' | 'N' | 'F'

export const PART_SETTLEMENT_TYPES = ['有償支給', '無償支給', '自給', 'その他'] as const
export type PartSettlementType = (typeof PART_SETTLEMENT_TYPES)[number]

export interface PartMasterRow {
  id: number
  part_cd: string
  part_name: string
  category?: string | null
  kind: PartKind
  settlement_type: PartSettlementType
  uom: string
  unit_price: number
  material_unit_price: number
  /** 単価+材料（原通貨）、DB 計算列 */
  total_unit_price: number
  currency: string
  exchange_rate: number
  /** 総単価（円）＝単価×為替(>0)＋部品材料単価 */
  standard_price_jpy: number
  supplier_cd?: string | null
  supplier_name?: string | null
  status: number
  remarks?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface PartMasterPayload {
  part_cd: string
  part_name: string
  category?: string | null
  kind?: PartKind
  settlement_type?: PartSettlementType
  uom?: string
  unit_price?: number
  material_unit_price?: number
  currency?: string
  exchange_rate?: number
  supplier_cd?: string | null
  status?: number
  remarks?: string | null
}

export function getPartList(params: {
  keyword?: string
  status?: number
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

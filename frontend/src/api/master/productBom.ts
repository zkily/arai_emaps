/**
 * 明細BOM API
 */
import request from '@/shared/api/request'

export interface BomLinePayload {
  parent_line_id?: number | null
  line_no: number
  component_type: string
  component_product_cd?: string | null
  component_material_cd?: string | null
  qty_per: number
  uom: string
  scrap_rate?: number
  consume_process_cd?: string | null
  consume_step_no?: number | null
  remarks?: string | null
}

export interface BomHeaderPayload {
  parent_product_cd: string
  bom_type?: string
  revision?: string
  status?: string
  effective_from?: string | null
  effective_to?: string | null
  base_quantity?: number
  uom?: string
  remarks?: string | null
  lines?: BomLinePayload[]
}

export interface BomLine extends BomLinePayload {
  id: number
  header_id: number
  children?: BomLine[]
}

export interface BomHeader {
  id: number
  parent_product_cd: string
  bom_type: string
  revision: string
  status: string
  effective_from: string | null
  effective_to: string | null
  base_quantity: number
  uom: string
  remarks: string | null
  lines?: BomLine[]
}

export function getBomHeaders(params: Record<string, unknown>) {
  return request.get('/api/master/product-bom', { params }) as Promise<{ success: boolean; data: { list: BomHeader[]; total: number } }>
}

export function getBomHeader(id: number) {
  return request.get(`/api/master/product-bom/${id}`) as Promise<{ success: boolean; data: BomHeader }>
}

export function createBomHeader(data: BomHeaderPayload) {
  return request.post('/api/master/product-bom', data) as Promise<{ success: boolean; data: BomHeader }>
}

export function updateBomHeader(id: number, data: BomHeaderPayload) {
  return request.put(`/api/master/product-bom/${id}`, data) as Promise<{ success: boolean }>
}

export function deleteBomHeader(id: number) {
  return request.delete(`/api/master/product-bom/${id}`) as Promise<{ success: boolean }>
}

export function getBomTree(headerId: number) {
  return request.get(`/api/master/product-bom/${headerId}/tree`) as Promise<{
    success: boolean
    data: { header: BomHeader; tree: BomLine[] }
  }>
}

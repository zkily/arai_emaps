/**
 * 工程別標準原価増分 API
 */
import request from '@/shared/api/request'

export interface UnitPricePayload {
  product_cd: string
  route_cd: string
  step_no: number
  line_seq?: number
  line_type?: string
  description?: string | null
  increment_unit_price: number
  currency?: string
  effective_from?: string | null
  effective_to?: string | null
  status?: string
  bom_line_id?: number | null
  remarks?: string | null
}

export interface UnitPriceRow extends UnitPricePayload {
  id: number
  cumulative_unit_price?: number
  created_by?: string | null
  updated_by?: string | null
}

export function getUnitPrices(params: Record<string, unknown>) {
  return request.get('/api/master/product-process-unit-prices', { params }) as Promise<{
    success: boolean
    data: { list: UnitPriceRow[]; total: number }
  }>
}

export function createUnitPrice(data: UnitPricePayload) {
  return request.post('/api/master/product-process-unit-prices', data) as Promise<{
    success: boolean
    data: UnitPriceRow
  }>
}

export function batchSaveUnitPrices(items: UnitPricePayload[]) {
  return request.post('/api/master/product-process-unit-prices/batch', { items }) as Promise<{
    success: boolean
    data: UnitPriceRow[]
  }>
}

export function updateUnitPrice(id: number, data: UnitPricePayload) {
  return request.put(`/api/master/product-process-unit-prices/${id}`, data) as Promise<{
    success: boolean
    data: UnitPriceRow
  }>
}

export function deleteUnitPrice(id: number) {
  return request.delete(`/api/master/product-process-unit-prices/${id}`) as Promise<{ success: boolean }>
}

export function getCumulativePrices(params: { product_cd: string; route_cd: string; target_date?: string }) {
  return request.get('/api/master/product-process-unit-prices/cumulative', { params }) as Promise<{
    success: boolean
    data: UnitPriceRow[]
  }>
}

/**
 * 工程加工費マスタ API
 */
import request from '@/shared/api/request'

export interface ProcessProcessingFeePayload {
  process_cd: string
  method_cd: string
  method_name?: string | null
  unit_price: number
  currency?: string
  charge_uom?: string
  effective_from?: string | null
  effective_to?: string | null
  status?: string
  remarks?: string | null
}

export interface ProcessProcessingFeeRow extends ProcessProcessingFeePayload {
  id: number
  process_name?: string | null
  created_by?: string | null
  updated_by?: string | null
}

export function getProcessProcessingFees(params: Record<string, unknown>) {
  return request.get('/api/master/process-processing-fees', { params }) as Promise<{
    success: boolean
    data: { list: ProcessProcessingFeeRow[]; total: number }
  }>
}

export function getProcessProcessingFee(id: number) {
  return request.get(`/api/master/process-processing-fees/${id}`) as Promise<{
    success: boolean
    data: ProcessProcessingFeeRow
  }>
}

export function createProcessProcessingFee(data: ProcessProcessingFeePayload) {
  return request.post('/api/master/process-processing-fees', data) as Promise<{
    success: boolean
    data: ProcessProcessingFeeRow
  }>
}

export function updateProcessProcessingFee(id: number, data: ProcessProcessingFeePayload) {
  return request.put(`/api/master/process-processing-fees/${id}`, data) as Promise<{
    success: boolean
    data: ProcessProcessingFeeRow
  }>
}

export function deleteProcessProcessingFee(id: number) {
  return request.delete(`/api/master/process-processing-fees/${id}`) as Promise<{
    success: boolean
    message?: string
  }>
}

/**
 * 工程別不良項目マスタ API
 */
import request from '@/shared/api/request'

export interface ProcessDefectItem {
  id?: number
  detection_process_cd: string
  attributable_process_cd: string
  defect_cd: string
  defect_name: string
  sort_order?: number
  status?: string
  remarks?: string | null
  detection_process_name?: string
  attributable_process_name?: string
  created_at?: string
  updated_at?: string
}

export interface ProcessDefectItemListParams {
  detectionProcessCd?: string
  attributableProcessCd?: string
  keyword?: string
  status?: string
  activeOnly?: boolean
  page?: number
  pageSize?: number
}

export interface ProcessDefectItemListResponse {
  success?: boolean
  data?: { list: ProcessDefectItem[]; total: number }
}

const BASE = '/api/master/process-defect-items'

export function fetchProcessDefectItems(
  params?: ProcessDefectItemListParams
): Promise<ProcessDefectItemListResponse> {
  return request.get(BASE, { params }) as Promise<ProcessDefectItemListResponse>
}

/** MES 等：収集工程の有効不良項目のみ取得 */
export function fetchProcessDefectItemOptions(
  detectionProcessCd: string,
  attributableProcessCd?: string
): Promise<{ success?: boolean; data?: ProcessDefectItem[] }> {
  return request.get(`${BASE}/options`, {
    params: {
      detectionProcessCd,
      ...(attributableProcessCd ? { attributableProcessCd } : {}),
    },
  }) as Promise<{ success?: boolean; data?: ProcessDefectItem[] }>
}

export function getProcessDefectItemById(id: number): Promise<{ success?: boolean; data?: ProcessDefectItem }> {
  return request.get(`${BASE}/${id}`) as Promise<{ success?: boolean; data?: ProcessDefectItem }>
}

export function createProcessDefectItem(
  data: Partial<ProcessDefectItem>
): Promise<{ success?: boolean; data?: ProcessDefectItem }> {
  return request.post(BASE, data) as Promise<{ success?: boolean; data?: ProcessDefectItem }>
}

export function updateProcessDefectItem(
  id: number,
  data: Partial<ProcessDefectItem>
): Promise<{ success?: boolean; data?: ProcessDefectItem }> {
  return request.put(`${BASE}/${id}`, data) as Promise<{ success?: boolean; data?: ProcessDefectItem }>
}

export function deleteProcessDefectItem(id: number): Promise<{ success?: boolean; message?: string }> {
  return request.delete(`${BASE}/${id}`) as Promise<{ success?: boolean; message?: string }>
}

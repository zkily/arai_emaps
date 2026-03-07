/**
 * 工程マスタ API
 */
import request from '@/shared/api/request'
import type { ProcessItem } from '@/types/master'

export interface ProcessListParams {
  keyword?: string
  category?: string
  is_outsource?: boolean
  page?: number
  pageSize?: number
}

export interface ProcessListResponse {
  success?: boolean
  data?: { list: ProcessItem[]; total: number }
  list?: ProcessItem[]
  total?: number
}

/** 工程一覧取得 */
export function fetchProcesses(params: ProcessListParams = {}): Promise<ProcessListResponse> {
  return request.get('/api/master/processes', { params }) as Promise<ProcessListResponse>
}

/** 工程一覧取得（getProcessOptions 用） */
export function getProcessList(params: { page?: number; pageSize?: number } = {}): Promise<ProcessListResponse> {
  return request.get('/api/master/processes', {
    params: { page: params.page ?? 1, pageSize: params.pageSize ?? 5000 },
  }) as Promise<ProcessListResponse>
}

/** 工程CDで1件取得 */
export function getProcessByCd(processCd: string): Promise<ProcessItem> {
  return request.get(`/api/master/processes/by-cd/${encodeURIComponent(processCd)}`) as Promise<ProcessItem>
}

/** 工程IDで1件取得（オプション・詳細用） */
export function getProcessByIdOrCd(idOrCd: number | string): Promise<ProcessItem> {
  if (typeof idOrCd === 'number') {
    return request.get(`/api/master/processes/${idOrCd}`) as Promise<ProcessItem>
  }
  return getProcessByCd(String(idOrCd))
}

/** 工程新規登録 */
export function createProcess(data: Partial<ProcessItem>): Promise<ProcessItem> {
  return request.post('/api/master/processes', data) as Promise<ProcessItem>
}

/** 工程更新 */
export function updateProcess(id: number, data: Partial<ProcessItem>): Promise<ProcessItem> {
  return request.put(`/api/master/processes/${id}`, data) as Promise<ProcessItem>
}

/** 工程削除 */
export function deleteProcess(id: number): Promise<{ message: string }> {
  return request.delete(`/api/master/processes/${id}`) as Promise<{ message: string }>
}

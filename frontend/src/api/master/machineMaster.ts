/**
 * 設備マスタ API
 */
import request from '@/shared/api/request'
import type { MachineItem } from '@/types/master'

export interface MachineListParams {
  keyword?: string
  machine_type?: string
  status?: string
  page?: number
  pageSize?: number
}

export interface MachineListResponse {
  success?: boolean
  data?: { list: MachineItem[]; total: number }
  list?: MachineItem[]
  total?: number
}

/** 設備一覧取得 */
export function getMachineList(params: MachineListParams = {}): Promise<MachineListResponse> {
  return request.get('/api/master/machines', { params }) as Promise<MachineListResponse>
}

/** 設備オプション（稼働中など） */
export function getMachineOptions(status?: string): Promise<{ cd: string; name: string }[]> {
  return request.get('/api/master/machines/options', { params: status ? { status } : {} }) as Promise<{ cd: string; name: string }[]>
}

/** 設備1件取得 */
export function getMachineById(id: number): Promise<MachineItem> {
  return request.get(`/api/master/machines/${id}`) as Promise<MachineItem>
}

/** 設備新規登録 */
export function createMachine(data: Partial<MachineItem>): Promise<MachineItem> {
  return request.post('/api/master/machines', data) as Promise<MachineItem>
}

/** 設備更新 */
export function updateMachine(data: Partial<MachineItem> & { id: number }): Promise<MachineItem> {
  return request.put(`/api/master/machines/${data.id}`, data) as Promise<MachineItem>
}

/** 設備削除 */
export function deleteMachineById(id: number): Promise<{ message: string }> {
  return request.delete(`/api/master/machines/${id}`) as Promise<{ message: string }>
}

/**
 * 運送便マスタ API
 */
import request from '@/shared/api/request'
import type { CarrierItem } from '@/types/master'

export interface CarrierListParams {
  keyword?: string
  status?: number
  page?: number
  pageSize?: number
}

export interface CarrierListResponse {
  success?: boolean
  data?: { list: CarrierItem[]; total: number }
  list?: CarrierItem[]
  total?: number
}

/** 運送便一覧取得 */
export function getCarrierList(params: CarrierListParams = {}): Promise<CarrierListResponse> {
  return request.get('/api/master/carriers', { params }) as Promise<CarrierListResponse>
}

/** 運送便オプション（有効のみ） */
export function getCarrierOptions(): Promise<{ cd: string; name: string }[]> {
  return request.get('/api/master/carriers/options') as Promise<{ cd: string; name: string }[]>
}

/** 運送便1件取得 */
export function getCarrierById(id: number): Promise<CarrierItem> {
  return request.get(`/api/master/carriers/${id}`) as Promise<CarrierItem>
}

/** 運送便新規登録 */
export function createCarrier(data: Partial<CarrierItem>): Promise<CarrierItem> {
  return request.post('/api/master/carriers', data) as Promise<CarrierItem>
}

/** 運送便更新 */
export function updateCarrier(data: Partial<CarrierItem> & { id: number }): Promise<CarrierItem> {
  return request.put(`/api/master/carriers/${data.id}`, data) as Promise<CarrierItem>
}

/** 運送便状態更新 */
export function updateCarrierStatus(id: number, status: number): Promise<CarrierItem> {
  return request.patch(`/api/master/carriers/${id}/status?status=${status}`) as Promise<CarrierItem>
}

/** 運送便削除 */
export function deleteCarrierById(id: number): Promise<{ message: string }> {
  return request.delete(`/api/master/carriers/${id}`) as Promise<{ message: string }>
}

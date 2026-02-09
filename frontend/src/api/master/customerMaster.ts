/**
 * 顧客マスタ API
 */
import request from '@/shared/api/request'
import type { CustomerItem } from '@/types/master'

export interface CustomerListParams {
  keyword?: string
  status?: number
  customer_type?: string
  page?: number
  pageSize?: number
}

export interface CustomerListResponse {
  success?: boolean
  data?: { list: CustomerItem[]; total: number }
  list?: CustomerItem[]
  total?: number
}

/** 顧客一覧取得 */
export function getCustomerList(params: CustomerListParams = {}): Promise<CustomerListResponse> {
  return request.get('/api/master/customers', { params }) as Promise<CustomerListResponse>
}

/** 顧客オプション（有効のみ） */
export function getCustomerOptions(): Promise<{ cd: string; name: string }[]> {
  return request.get('/api/master/customers/options') as Promise<{ cd: string; name: string }[]>
}

/** 顧客1件取得 */
export function getCustomerById(id: number): Promise<CustomerItem> {
  return request.get(`/api/master/customers/${id}`) as Promise<CustomerItem>
}

/** 顧客新規登録 */
export function createCustomer(data: Partial<CustomerItem>): Promise<CustomerItem> {
  return request.post('/api/master/customers', data) as Promise<CustomerItem>
}

/** 顧客更新 */
export function updateCustomer(data: Partial<CustomerItem> & { id: number }): Promise<CustomerItem> {
  return request.put(`/api/master/customers/${data.id}`, data) as Promise<CustomerItem>
}

/** 顧客状態更新 */
export function updateCustomerStatus(id: number, status: number): Promise<CustomerItem> {
  return request.patch(`/api/master/customers/${id}/status?status=${status}`) as Promise<CustomerItem>
}

/** 顧客削除 */
export function deleteCustomerById(id: number): Promise<{ message: string }> {
  return request.delete(`/api/master/customers/${id}`) as Promise<{ message: string }>
}

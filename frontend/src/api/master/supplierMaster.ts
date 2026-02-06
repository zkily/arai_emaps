/**
 * 仕入先マスタ API
 */
import request from '@/shared/api/request'
import type { Supplier } from '@/types/master'

export interface SupplierListParams {
  keyword?: string
  page?: number
  pageSize?: number
}

export interface SupplierListResponse {
  success?: boolean
  data?: { list: Supplier[]; total: number }
  list?: Supplier[]
  total?: number
}

export function getSupplierList(params?: SupplierListParams): Promise<SupplierListResponse> {
  return request.get('/api/master/suppliers', { params }) as Promise<SupplierListResponse>
}

export function getSupplierById(id: number): Promise<Supplier> {
  return request.get(`/api/master/suppliers/${id}`) as Promise<Supplier>
}

export function createSupplier(data: Supplier): Promise<Supplier> {
  return request.post('/api/master/suppliers', data) as Promise<Supplier>
}

export function updateSupplier(data: Supplier): Promise<Supplier> {
  if (!data.id) return Promise.reject(new Error('id is required'))
  return request.put(`/api/master/suppliers/${data.id}`, data) as Promise<Supplier>
}

export function deleteSupplier(id: number): Promise<{ message: string }> {
  return request.delete(`/api/master/suppliers/${id}`) as Promise<{ message: string }>
}

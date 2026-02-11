/**
 * 製品機器設定マスタ API
 */
import request from '@/shared/api/request'

export interface ProductMachineConfig {
  id?: number
  product_cd: string
  product_name: string
  cutting_machine?: string
  chamfering_machine?: string
  molding_machine?: string
  plating_machine?: string
  welding_machine?: string
  inspector_machine?: string
  outsourced_plating_machine?: string
  outsourced_welding_machine?: string
  created_at?: string
  updated_at?: string
}

export interface AvailableProduct {
  product_cd: string
  product_name: string
}

export interface ProductMachineConfigListParams {
  keyword?: string
  limit?: number
}

const BASE = '/api/master/product-machine-config'

export function fetchProductMachineConfigList(
  params?: ProductMachineConfigListParams
): Promise<{ success?: boolean; data?: { list: ProductMachineConfig[]; total: number }; list?: ProductMachineConfig[]; total?: number }> {
  return request.get(BASE, { params }) as Promise<any>
}

export function fetchAvailableProducts(): Promise<{ success?: boolean; data?: AvailableProduct[] }> {
  return request.get(`${BASE}/available-products`) as Promise<any>
}

export function getProductMachineConfigById(id: number): Promise<ProductMachineConfig> {
  return request.get(`${BASE}/${id}`) as Promise<ProductMachineConfig>
}

export function createProductMachineConfig(data: Partial<ProductMachineConfig>): Promise<ProductMachineConfig> {
  return request.post(BASE, data) as Promise<ProductMachineConfig>
}

export function updateProductMachineConfig(
  id: number,
  data: Partial<ProductMachineConfig>
): Promise<ProductMachineConfig> {
  return request.put(`${BASE}/${id}`, data) as Promise<ProductMachineConfig>
}

export function deleteProductMachineConfig(id: number): Promise<{ message: string }> {
  return request.delete(`${BASE}/${id}`) as Promise<{ message: string }>
}

export function syncProducts(): Promise<{ success?: boolean; data?: { added: number; updated: number; total: number } }> {
  return request.post(`${BASE}/sync`) as Promise<any>
}

/**
 * ERP 顧客・納入先・製品の一覧取得（オプション用）
 * 旧 @/api/order の getCustomers / getDestinations / getProducts を /api/erp に移行
 */
import request from '@/utils/request'

const BASE = '/api/erp'

export interface CustomerItem {
  id?: number
  customer_code: string
  customer_name: string
  customer_name_kana?: string
  is_active?: boolean
}

export interface DestinationItem {
  id?: number
  destination_code: string
  destination_name: string
  destination_name_kana?: string
  customer_code?: string
  is_active?: boolean
}

export interface ProductItem {
  id?: number
  product_code: string
  product_name: string
  product_name_kana?: string
  is_active?: boolean
}

/** 顧客一覧（ERP API） */
export async function getCustomers(): Promise<CustomerItem[]> {
  const res = await request.get<CustomerItem[]>(`${BASE}/customers`)
  return Array.isArray(res) ? res : (res as { data?: CustomerItem[] })?.data ?? []
}

/** 納入先一覧（ERP API、customer_code で絞り込み可） */
export async function getDestinations(customerCode?: string): Promise<DestinationItem[]> {
  const params = customerCode ? { customer_code: customerCode } : undefined
  const res = await request.get<DestinationItem[]>(`${BASE}/destinations`, { params })
  return Array.isArray(res) ? res : (res as { data?: DestinationItem[] })?.data ?? []
}

/** 製品一覧（ERP API） */
export async function getProducts(): Promise<ProductItem[]> {
  const res = await request.get<ProductItem[]>(`${BASE}/products`)
  return Array.isArray(res) ? res : (res as { data?: ProductItem[] })?.data ?? []
}

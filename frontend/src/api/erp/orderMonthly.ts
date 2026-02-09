/**
 * 月別受注 API（受注管理）
 */
import request from '@/utils/request'

const BASE = '/api/erp/orders/monthly'

export interface OrderMonthlyItem {
  id: number
  order_id: string
  destination_cd: string
  destination_name: string
  year: number
  month: number
  product_cd: string
  product_name: string
  product_alias?: string
  product_type: string
  forecast_units: number
  forecast_total_units: number
  forecast_diff: number
  created_at: string
  updated_at: string
}

export interface OrderMonthlyCreate {
  destination_cd: string
  destination_name: string
  year: number
  month: number
  product_cd: string
  product_name: string
  product_alias?: string
  product_type?: string
  forecast_units?: number
  forecast_total_units?: number
  forecast_diff?: number
}

export interface OrderMonthlyFilters {
  year?: number
  month?: number
  destination_cd?: string
  product_cd?: string
  keyword?: string
}

export function fetchOrderMonthlyList(params?: OrderMonthlyFilters): Promise<OrderMonthlyItem[]> {
  return request.get(BASE, { params }).then((res: any) => (Array.isArray(res) ? res : res?.data ?? []))
}

export function createOrderMonthly(data: OrderMonthlyCreate): Promise<OrderMonthlyItem> {
  return request.post(BASE, data)
}

export function getOrderMonthlyById(id: number): Promise<OrderMonthlyItem> {
  return request.get(`${BASE}/${id}`)
}

export function getOrderMonthlyByOrderId(orderId: string): Promise<OrderMonthlyItem> {
  return request.get(`${BASE}/by-order-id/${encodeURIComponent(orderId)}`)
}

export function updateOrderMonthly(id: number, data: Partial<OrderMonthlyCreate>): Promise<OrderMonthlyItem> {
  return request.put(`${BASE}/${id}`, data)
}

export function deleteOrderMonthly(id: number): Promise<void> {
  return request.delete(`${BASE}/${id}`)
}

/**
 * 外注管理API（メッキ・溶接注文/受入/支給材料/在庫）
 * バックエンド /api/outsourcing を利用
 */
import request from '@/utils/request'

const BASE = '/api/outsourcing'

export interface OutsourcingSupplier {
  id: number
  supplier_cd: string
  supplier_name: string
  supplier_type: string
  is_active?: boolean
  [key: string]: unknown
}

export interface PlatingOrder {
  id?: number
  order_no?: string
  order_date?: string
  supplier_cd?: string
  product_cd?: string
  product_name?: string
  plating_type?: string
  quantity?: number
  unit_price?: number
  delivery_date?: string
  status?: string
  [key: string]: unknown
}

export interface PlatingReceiving {
  id?: number
  receiving_no?: string
  receiving_date?: string
  order_id?: number
  order_no?: string
  supplier_cd?: string
  product_cd?: string
  product_name?: string
  plating_type?: string
  order_qty?: number
  receiving_qty?: number
  good_qty?: number
  defect_qty?: number
  status?: string
  inspector?: string
  [key: string]: unknown
}

export interface WeldingOrder {
  id?: number
  order_no?: string
  order_date?: string
  supplier_cd?: string
  product_cd?: string
  product_name?: string
  welding_type?: string
  quantity?: number
  unit_price?: number
  delivery_date?: string
  status?: string
  [key: string]: unknown
}

export interface WeldingReceiving {
  id?: number
  receiving_no?: string
  receiving_date?: string
  order_id?: number
  order_no?: string
  supplier_cd?: string
  product_cd?: string
  product_name?: string
  welding_type?: string
  order_qty?: number
  receiving_qty?: number
  good_qty?: number
  defect_qty?: number
  status?: string
  inspector?: string
  [key: string]: unknown
}

// ========== ダッシュボード ==========
export function getOutsourcingDashboard() {
  return request.get<{ success: boolean; data: Record<string, unknown> }>(`${BASE}/dashboard`)
}

export function getUpcomingDeliveries(days: number) {
  return request.get<{ success: boolean; data: unknown[] }>(`${BASE}/upcoming-deliveries`, { params: { days } })
}

export function getSupplierSummary() {
  return request.get<{ success: boolean; data: unknown[] }>(`${BASE}/suppliers/summary`)
}

// ========== 外注先マスタ ==========
export function getSuppliers(params?: { type?: string; isActive?: boolean }) {
  return request.get<{ success?: boolean; data?: OutsourcingSupplier[] }>(`${BASE}/suppliers`, { params })
}

export function createSupplier(data: Partial<OutsourcingSupplier>) {
  return request.post<{ success: boolean; data: OutsourcingSupplier }>(`${BASE}/suppliers`, data)
}

export function updateSupplier(id: number, data: Partial<OutsourcingSupplier>) {
  return request.put<{ success: boolean; data: OutsourcingSupplier }>(`${BASE}/suppliers/${id}`, data)
}

export function deleteSupplier(id: number) {
  return request.delete<{ success: boolean; message?: string }>(`${BASE}/suppliers/${id}`)
}

// ========== メッキ注文 ==========
export function getPlatingOrders(params?: Record<string, unknown>) {
  return request.get<{ success?: boolean; data?: PlatingOrder[] }>(`${BASE}/plating/orders`, { params })
}

export function createPlatingOrder(data: Partial<PlatingOrder>) {
  return request.post<{ success: boolean; data: PlatingOrder }>(`${BASE}/plating/orders`, data)
}

export function updatePlatingOrder(id: number, data: Partial<PlatingOrder>) {
  return request.put<{ success: boolean; data: PlatingOrder }>(`${BASE}/plating/orders/${id}`, data)
}

export function deletePlatingOrder(id: number) {
  return request.delete(`${BASE}/plating/orders/${id}`)
}

export function getPlatingOrdersByOrderNo(orderNo: string) {
  return request.get<{ success?: boolean; data?: PlatingOrder[] }>(`${BASE}/plating/orders/by-order-no`, { params: { order_no: orderNo } })
}

export function batchOrderPlating(orderIds: number[]) {
  return request.post<{ success: boolean }>(`${BASE}/plating/orders/batch-order`, { order_ids: orderIds })
}

// ========== メッキ受入 ==========
export function getPlatingReceivings(params?: Record<string, unknown>) {
  return request.get<{ success?: boolean; data?: PlatingReceiving[] }>(`${BASE}/plating/receivings`, { params })
}

export function createPlatingReceiving(data: Partial<PlatingReceiving>) {
  return request.post<{ success: boolean; data: PlatingReceiving }>(`${BASE}/plating/receivings`, data)
}

export function updatePlatingReceiving(id: number, data: Partial<PlatingReceiving>) {
  return request.put<{ success: boolean; data: PlatingReceiving }>(`${BASE}/plating/receivings/${id}`, data)
}

export function getPendingPlatingOrders() {
  return request.get<{ success?: boolean; data?: PlatingOrder[] }>(`${BASE}/plating/orders/pending`)
}

// ========== 溶接注文 ==========
export function getWeldingOrders(params?: Record<string, unknown>) {
  return request.get<{ success?: boolean; data?: WeldingOrder[] }>(`${BASE}/welding/orders`, { params })
}

export function createWeldingOrder(data: Partial<WeldingOrder>) {
  return request.post<{ success: boolean; data: WeldingOrder }>(`${BASE}/welding/orders`, data)
}

/** 溶接注文一括新規登録（1リクエストで複数件、order_no 重複を防ぐ） */
export function createWeldingOrdersBatch(orders: Partial<WeldingOrder>[]) {
  return request.post<{ success: boolean; data: WeldingOrder[]; count: number }>(
    `${BASE}/welding/orders/batch`,
    { orders },
  )
}

export function updateWeldingOrder(id: number, data: Partial<WeldingOrder>) {
  return request.put<{ success: boolean; data: WeldingOrder }>(`${BASE}/welding/orders/${id}`, data)
}

export function deleteWeldingOrder(id: number) {
  return request.delete(`${BASE}/welding/orders/${id}`)
}

export function getWeldingOrdersByOrderNo(orderNo: string) {
  return request.get<{ success?: boolean; data?: WeldingOrder[] }>(`${BASE}/welding/orders/by-order-no`, { params: { order_no: orderNo } })
}

export function batchOrderWelding(orderIds: number[]) {
  return request.post<{ success: boolean }>(`${BASE}/welding/orders/batch-order`, { order_ids: orderIds })
}

// ========== 溶接受入 ==========
export function getWeldingReceivings(params?: Record<string, unknown>) {
  return request.get<{ success?: boolean; data?: WeldingReceiving[] }>(`${BASE}/welding/receivings`, { params })
}

export function createWeldingReceiving(data: Partial<WeldingReceiving>) {
  return request.post<{ success: boolean; data: WeldingReceiving }>(`${BASE}/welding/receivings`, data)
}

export function updateWeldingReceiving(id: number, data: Partial<WeldingReceiving>) {
  return request.put<{ success: boolean; data: WeldingReceiving }>(`${BASE}/welding/receivings/${id}`, data)
}

export function getPendingWeldingOrders() {
  return request.get<{ success?: boolean; data?: WeldingOrder[] }>(`${BASE}/welding/orders/pending`)
}

// ========== 外注在庫・履歴 ==========
export function getPlatingStock(params?: Record<string, unknown>) {
  return request.get<{ success?: boolean; data?: unknown[] }>(`${BASE}/plating/stock`, { params })
}

export function getWeldingStock(params?: Record<string, unknown>) {
  return request.get<{ success?: boolean; data?: unknown[] }>(`${BASE}/welding/stock`, { params })
}

export function getOutsourcingStockHistory(params: { processType: string; productCd: string; supplierCd: string; weldingType?: string }) {
  return request.get<{ success?: boolean; data?: unknown[] }>(`${BASE}/stock/history`, { params })
}

// ========== 工程製品・納入日 ==========
export function getProcessProducts(params: { processType: string; supplierCd: string; isActive?: boolean }) {
  return request.get<{ success?: boolean; data?: unknown[] }>(`${BASE}/process-products`, { params })
}

/** 納入先休日（master の納入先休日 API を利用） */
export function getDestinationHolidays(destinationCd?: string) {
  if (!destinationCd || String(destinationCd).trim() === '') {
    return Promise.resolve({ data: [] as { holiday_date?: string; holidayDate?: string }[] })
  }
  return request.get<{ holiday_date?: string; holidayDate?: string }[]>(`/api/master/destinations/holidays/by-destination/${encodeURIComponent(destinationCd)}`)
}

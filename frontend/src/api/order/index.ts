/**
 * 受注管理 API
 * Order Management API
 */
import request from '../request'

// ========== 型定義 ==========

export interface OrderMonthly {
  id?: number
  year: number
  month: number
  customer_code: string
  customer_name?: string
  product_code: string
  product_name?: string
  destination_code?: string
  destination_name?: string
  forecast_units?: number
  confirmed_units?: number
  forecast_diff?: number
  plating_type?: string
  plating_count?: number
  welding_type?: string
  welding_count?: number
  unit_price?: number
  total_amount?: number
  remarks?: string
  is_active?: boolean
  created_at?: string
  updated_at?: string
  created_by?: string
  updated_by?: string
}

export interface OrderDaily {
  id?: number
  monthly_order_id?: number
  year: number
  month: number
  day: number
  order_date: string
  customer_code: string
  customer_name?: string
  product_code: string
  product_name?: string
  destination_code?: string
  destination_name?: string
  confirmed_boxes?: number
  confirmed_units?: number
  forecast_units?: number
  shipped_boxes?: number
  shipped_units?: number
  shipping_status?: string
  confirmation_status?: string
  is_shipped?: boolean
  is_confirmed?: boolean
  unit_price?: number
  total_amount?: number
  remarks?: string
  is_active?: boolean
  created_at?: string
  updated_at?: string
  created_by?: string
  updated_by?: string
}

export interface Customer {
  id?: number
  customer_code: string
  customer_name: string
  customer_name_kana?: string
  postal_code?: string
  address?: string
  phone?: string
  fax?: string
  email?: string
  contact_person?: string
  contact_phone?: string
  contact_email?: string
  remarks?: string
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface Destination {
  id?: number
  destination_code: string
  destination_name: string
  destination_name_kana?: string
  customer_code?: string
  customer_name?: string
  postal_code?: string
  address?: string
  phone?: string
  remarks?: string
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface Product {
  id?: number
  product_code: string
  product_name: string
  product_name_kana?: string
  category?: string
  specification?: string
  unit?: string
  standard_price?: number
  cost_price?: number
  remarks?: string
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface OrderLog {
  id: number
  order_type: string
  order_id: number
  action: string
  old_data?: string
  new_data?: string
  user_id?: number
  user_name?: string
  ip_address?: string
  created_at: string
}

export interface OrderMonthlySummary {
  forecast_units: number
  confirmed_units: number
  forecast_total_units: number
  forecast_diff: number
  plating_count: number
  external_plating_count: number
  internal_welding_count: number
  external_welding_count: number
}

export interface OrderDailySummary {
  total_confirmed_boxes: number
  total_confirmed_units: number
  total_forecast_units: number
  shipped_orders_count: number
  unshipped_orders_count: number
  confirmed_orders_count: number
  unconfirmed_orders_count: number
}

export interface PaginatedResponse<T> {
  total: number
  page: number
  page_size: number
  total_pages: number
  items: T[]
}

export interface OrderMonthlyFilters {
  year?: number
  month?: number
  customer_code?: string
  product_code?: string
  page?: number
  page_size?: number
}

export interface OrderDailyFilters {
  year?: number
  month?: number
  day?: number
  monthly_order_id?: number
  customer_code?: string
  product_code?: string
  shipping_status?: string
  confirmation_status?: string
  page?: number
  page_size?: number
}

// ========== 月別受注 API ==========

export const getMonthlyOrders = (filters: OrderMonthlyFilters = {}) => {
  return request.get<PaginatedResponse<OrderMonthly>>('/api/erp/orders/monthly', { params: filters })
}

export const getMonthlyOrdersSummary = (year?: number, month?: number) => {
  return request.get<OrderMonthlySummary>('/api/erp/orders/monthly/summary', {
    params: { year, month },
  })
}

export const getMonthlyOrder = (orderId: number) => {
  return request.get<OrderMonthly>(`/api/erp/orders/monthly/${orderId}`)
}

export const createMonthlyOrder = (data: OrderMonthly) => {
  return request.post<OrderMonthly>('/api/erp/orders/monthly', data)
}

export const updateMonthlyOrder = (orderId: number, data: Partial<OrderMonthly>) => {
  return request.put<OrderMonthly>(`/api/erp/orders/monthly/${orderId}`, data)
}

export const deleteMonthlyOrder = (orderId: number) => {
  return request.delete(`/api/erp/orders/monthly/${orderId}`)
}

// ========== 日別受注 API ==========

export const getDailyOrders = (filters: OrderDailyFilters = {}) => {
  return request.get<PaginatedResponse<OrderDaily>>('/api/erp/orders/daily', { params: filters })
}

export const getDailyOrdersSummary = (year?: number, month?: number, day?: number) => {
  return request.get<OrderDailySummary>('/api/erp/orders/daily/summary', {
    params: { year, month, day },
  })
}

export const getDailyOrder = (orderId: number) => {
  return request.get<OrderDaily>(`/api/erp/orders/daily/${orderId}`)
}

export const createDailyOrder = (data: OrderDaily) => {
  return request.post<OrderDaily>('/api/erp/orders/daily', data)
}

export const createDailyOrdersBatch = (data: OrderDaily[]) => {
  return request.post<{ message: string; count: number }>('/api/erp/orders/daily/batch', data)
}

export const updateDailyOrder = (orderId: number, data: Partial<OrderDaily>) => {
  return request.put<OrderDaily>(`/api/erp/orders/daily/${orderId}`, data)
}

export const deleteDailyOrder = (orderId: number) => {
  return request.delete(`/api/erp/orders/daily/${orderId}`)
}

export async function fetchDailyOrdersByMonthlyOrderId(
  monthlyOrderId: number
): Promise<{ list: OrderDaily[] }> {
  const res = await getDailyOrders({
    monthly_order_id: monthlyOrderId,
    page_size: 999,
    page: 1,
  })
  return { list: res?.items ?? [] }
}

export interface BatchUpdateDailyOrderItem {
  id: number
  forecast_units?: number
  confirmed_boxes?: number
  confirmed_units?: number
  status?: string
  remarks?: string
}

export function batchUpdateDailyOrders(payload: { list: BatchUpdateDailyOrderItem[] }) {
  return request.put<{ message: string }>('/api/erp/orders/daily/batch', payload)
}

// ========== 顧客・納入先・製品マスタ ==========

export const getCustomers = () => {
  return request.get<Customer[]>('/api/erp/customers')
}

export const createCustomer = (data: Customer) => {
  return request.post<Customer>('/api/erp/customers', data)
}

export const getDestinations = (customerCode?: string) => {
  return request.get<Destination[]>('/api/erp/destinations', {
    params: { customer_code: customerCode },
  })
}

export const createDestination = (data: Destination) => {
  return request.post<Destination>('/api/erp/destinations', data)
}

export const getProducts = () => {
  return request.get<Product[]>('/api/erp/products')
}

export const createProduct = (data: Product) => {
  return request.post<Product>('/api/erp/products', data)
}

// ========== ログ ==========

export const getOrderLogs = (orderType?: string, orderId?: number, limit: number = 100) => {
  return request.get<OrderLog[]>('/api/erp/orders/logs', {
    params: { order_type: orderType, order_id: orderId, limit },
  })
}

// ========== ユーティリティ ==========

export const formatOrderForExport = (order: OrderDaily | OrderMonthly) => {
  return {
    ...order,
    order_date: order.order_date || `${order.year}/${order.month}`,
    total_amount: order.total_amount?.toFixed(2),
    unit_price: order.unit_price?.toFixed(2),
  }
}

export const extractDateParts = (date: Date | string) => {
  const d = typeof date === 'string' ? new Date(date) : date
  return {
    year: d.getFullYear(),
    month: d.getMonth() + 1,
    day: d.getDate(),
  }
}

export const formatOrderDate = (year: number, month: number, day?: number) => {
  const monthStr = String(month).padStart(2, '0')
  if (day) {
    const dayStr = String(day).padStart(2, '0')
    return `${year}-${monthStr}-${dayStr}`
  }
  return `${year}-${monthStr}`
}

// ========== エイリアス・拡張 ==========

export const fetchMonthlyOrders = getMonthlyOrders
export const fetchMonthlySummary = getMonthlyOrdersSummary
export const deleteMonthlyOrderByOrderId = deleteMonthlyOrder
export const fetchDailyOrders = getDailyOrders
export const addOrderDaily = createDailyOrder
export const fetchLogs = (orderType?: string, orderId?: number, limit?: number) =>
  getOrderLogs(orderType, orderId, limit ?? 100)
export const fetchDailyOrdersByDate = (params: { year: number; month: number; day?: number } & OrderDailyFilters) =>
  getDailyOrders({ ...params, page_size: params.page_size ?? 999 })
export const fetchDailyAllOrders = (filters: OrderDailyFilters = {}) =>
  getDailyOrders({ ...filters, page_size: filters.page_size ?? 9999 })

export async function checkMonthlyOrderExists(params: {
  year: number
  month: number
  customer_code: string
  product_code: string
  destination_code?: string
}): Promise<boolean> {
  const res = await getMonthlyOrders({
    year: params.year,
    month: params.month,
    customer_code: params.customer_code,
    product_code: params.product_code,
    page_size: 1,
  })
  return (res?.items?.length ?? 0) > 0
}

export async function checkCombinationExists(params: {
  year: number
  month: number
  customer_code: string
  product_code: string
  destination_code?: string
}): Promise<boolean> {
  return checkMonthlyOrderExists(params)
}

export async function getProductsByDestination(
  _destinationCode: string,
  _year?: number,
  _month?: number
): Promise<Product[]> {
  const list = await getProducts()
  return list ?? []
}

export async function generateDailyOrders(_monthlyOrderId: number): Promise<OrderDaily[]> {
  const res = await fetchDailyOrdersByMonthlyOrderId(_monthlyOrderId)
  return res.list ?? []
}

export function batchCreateMonthlyOrders(orders: OrderMonthly[]) {
  return Promise.all(orders.map((o) => createMonthlyOrder(o)))
}

export function updateOrderFields(orderId: number, data: Partial<OrderDaily>) {
  return updateDailyOrder(orderId, data)
}

export function batchUpdateMonthlyQuantity(_payload: { list: Array<{ id: number; [key: string]: unknown }> }) {
  return request.put<{ message: string }>('/api/erp/orders/monthly/batch-quantity', _payload)
}

export function updateOrderDailyStatus(_orderId: number, _status: string) {
  return request.put<OrderDaily>(`/api/erp/orders/daily/${_orderId}/status`, { status: _status })
}

export function syncShippingLog(_params: unknown) {
  return request.post<{ message: string }>('/api/erp/orders/daily/sync-shipping', _params)
}

export function confirmOrder(_orderId: number) {
  return request.post<{ message: string }>(`/api/erp/orders/daily/${_orderId}/confirm`)
}

export function fetchDashboardSummary(_params?: { year?: number; month?: number }) {
  return request.get<Record<string, unknown>>('/api/erp/orders/dashboard/summary', { params: _params })
}

export interface OrderHistoryComparisonItem {
  id?: number
  order_date?: string
  customer_code?: string
  product_code?: string
  destination_code?: string
  [key: string]: unknown
}

export function fetchOrderHistoryComparison(_params: unknown) {
  return request.get<OrderHistoryComparisonItem[]>('/api/erp/orders/history/comparison', { params: _params })
}

export function createOrderHistorySnapshot(_params: unknown) {
  return request.post<{ id: number }>('/api/erp/orders/history/snapshot', _params)
}

export function getForecastDiffRanking(params: { year: number; month: number }) {
  return request.get<Array<{ product_code: string; product_name: string; diff: number }>>(
    '/api/erp/orders/forecast-diff-rank',
    { params }
  )
}

export default {
  getMonthlyOrders,
  getMonthlyOrdersSummary,
  getMonthlyOrder,
  createMonthlyOrder,
  updateMonthlyOrder,
  deleteMonthlyOrder,
  getDailyOrders,
  getDailyOrdersSummary,
  getDailyOrder,
  createDailyOrder,
  createDailyOrdersBatch,
  updateDailyOrder,
  deleteDailyOrder,
  getCustomers,
  createCustomer,
  getDestinations,
  createDestination,
  getProducts,
  createProduct,
  getOrderLogs,
  formatOrderForExport,
  extractDateParts,
  formatOrderDate,
}

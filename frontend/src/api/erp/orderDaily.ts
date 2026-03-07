/**
 * 日別受注 API（日受注管理）
 */
import request from '@/utils/request'

const BASE = '/api/erp/orders/daily'

export interface OrderDailyItem {
  id: number
  monthly_order_id: string | null
  destination_cd: string
  destination_name: string | null
  date: string
  weekday: string | null
  product_cd: string
  product_name: string | null
  product_alias: string | null
  forecast_units: number
  confirmed_boxes: number
  confirmed_units: number
  created_at: string
  updated_at: string
  status: string | null
  remarks: string | null
  unit_per_box: number
  batch_id: number | null
  batch_no: string | null
  supply_status: string | null
  fulfilled_from_stock: number
  fulfilled_from_wip: number
  product_type: string | null
  confirmed: boolean
  confirmed_by: string | null
  confirmed_at: string | null
  delivery_date: string | null
  shipping_no: string | null
}

export interface OrderDailyCreate {
  monthly_order_id?: string | null
  destination_cd: string
  destination_name?: string | null
  date: string
  weekday?: string | null
  product_cd: string
  product_name?: string | null
  product_alias?: string | null
  forecast_units?: number
  confirmed_boxes?: number
  confirmed_units?: number
  status?: string | null
  remarks?: string | null
  unit_per_box?: number
  batch_id?: number | null
  batch_no?: string | null
  supply_status?: string | null
  fulfilled_from_stock?: number
  fulfilled_from_wip?: number
  product_type?: string | null
  confirmed?: boolean
  confirmed_by?: string | null
  confirmed_at?: string | null
  delivery_date?: string | null
  shipping_no?: string | null
}

export interface OrderDailyFilters {
  start_date?: string
  end_date?: string
  data_eq?: string
  monthly_order_id?: string
  destination_cd?: string
  keyword?: string
}

export function fetchOrderDailyList(params?: OrderDailyFilters): Promise<OrderDailyItem[]> {
  return request.get(BASE, { params }).then((res: any) => {
    const raw = Array.isArray(res) ? res : res?.data ?? res?.list
    if (Array.isArray(raw)) return raw
    if (raw && typeof raw === 'object' && !Array.isArray(raw)) return [raw]
    return []
  })
}

export function createOrderDaily(data: OrderDailyCreate): Promise<OrderDailyItem> {
  return request.post(BASE, data)
}

export function getOrderDailyById(id: number): Promise<OrderDailyItem> {
  return request.get(`${BASE}/${id}`)
}

export function updateOrderDaily(id: number, data: Partial<OrderDailyCreate>): Promise<OrderDailyItem> {
  return request.put(`${BASE}/${id}`, data)
}

export function deleteOrderDaily(id: number): Promise<void> {
  return request.delete(`${BASE}/${id}`)
}

// ========== 日次追加用：月次注文の存在チェック＆自動作成 ==========

export interface CheckMonthlyExistsResponse {
  exists: boolean
  id?: number
  order_id?: string
}

/** 月次注文IDで存在チェック */
export function checkMonthlyOrderExists(orderId: string): Promise<CheckMonthlyExistsResponse> {
  return request.get('/api/order/check-exists', { params: { order_id: orderId } }) as Promise<CheckMonthlyExistsResponse>
}

export interface AddMonthlyOrderData {
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
}

export interface AddMonthlyOrderResponse {
  ok: boolean
  order_id: string
  created: boolean
}

/** 月次注文の自動作成（日次追加時に月次が無い場合に呼び出す） */
export function addMonthlyOrder(data: AddMonthlyOrderData): Promise<AddMonthlyOrderResponse> {
  return request.post('/api/order/monthly/add', data) as Promise<AddMonthlyOrderResponse>
}

/** 日次注文を追加（POST /api/erp/orders/daily） — addOrderDaily は createOrderDaily のエイリアス */
export function addOrderDaily(data: OrderDailyCreate): Promise<OrderDailyItem> {
  return request.post(BASE, data)
}

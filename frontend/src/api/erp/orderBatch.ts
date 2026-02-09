/**
 * 受注バッチ API（月別一括登録の読込・存在チェック・一括登録）
 */
import request from '@/utils/request'

export interface OrderProductItem {
  product_cd: string
  product_name: string
  product_type: string
  forecast_units: number
}

export interface OrderProductsResponse {
  success: boolean
  data: OrderProductItem[]
}

export interface CheckCombinationExistsResponse {
  exists: boolean
  /** 既存の order_monthly.id（数量更新用） */
  id?: number
  /** 既存の forecast_units */
  forecast_units?: number
}

export interface BatchCreateProductItem {
  product_cd: string
  forecast_units: number
}

export interface BatchCreateMonthlyResponse {
  inserted: number
  total: number
  skipped: number
  message: string
}

/** 納入先+年月で製品一覧（order_monthly と LEFT JOIN で forecast_units 付き） */
export function getOrderProducts(params: {
  destination_cd: string
  year: number
  month: number
}): Promise<OrderProductsResponse> {
  return request.get('/api/order/products', { params }) as Promise<OrderProductsResponse>
}

/** 納入先名・製品名・年月の組み合わせが既存か */
export function checkCombinationExists(params: {
  destination_name: string
  product_name: string
  year: number
  month: number
}): Promise<CheckCombinationExistsResponse> {
  return request.get('/api/order/check-combination-exists', { params }) as Promise<CheckCombinationExistsResponse>
}

/** 月別受注一括登録 */
export function batchCreateMonthly(body: {
  year: number
  month: number
  destination_cd: string
  destination_name: string
  products: BatchCreateProductItem[]
}): Promise<BatchCreateMonthlyResponse> {
  return request.post('/api/order/batch-create-monthly', body) as Promise<BatchCreateMonthlyResponse>
}

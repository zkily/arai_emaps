/**
 * 生産サマリー（production_summarys）API
 */
import request from '@/utils/request'

const BASE = '/api/database/production-summarys'

export interface ProductionSummaryListParams {
  page?: number
  limit?: number
  startDate?: string
  endDate?: string
  productCd?: string
  keyword?: string
  sortBy?: string
  sortOrder?: 'ASC' | 'DESC'
}

export interface ProductionSummaryProduct {
  product_cd: string
  product_name?: string
}

/** 一覧取得（ページネーション） */
export function getProductionSummarysList(params: ProductionSummaryListParams) {
  return request.get(BASE, { params })
}

/** 製品一覧（重複なし） */
export function getProductionSummarysProducts() {
  return request.get(`${BASE}/products`)
}

export interface GenerateProductionSummarysParams {
  startDate: string
  endDate: string
}

/** データ生成（指定期間、既存はスキップ） */
export function generateProductionSummarys(params: GenerateProductionSummarysParams) {
  return request.post(`${BASE}/generate`, params)
}

export interface UpdateFromOrderDailyParams {
  updateMode?: 'all' | 'changed' | 'recent'
  days?: number
  clearBeforeUpdate?: boolean
}

/** 受注データから forecast_quantity / order_quantity を更新 */
export function updateProductionSummarysFromOrderDaily(params?: UpdateFromOrderDailyParams) {
  return request.post(`${BASE}/update-from-order-daily`, params || {})
}

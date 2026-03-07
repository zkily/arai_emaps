/**
 * 生産実績管理 API（在庫取引ログを工程・製品名・設備名付きで取得、更新・削除）
 */
import request from '@/shared/api/request'

const PRODUCTION_ACTUAL_BASE = '/api/erp/production-actual-logs'
const STOCK_LOG_BASE = '/api/erp/stock-transaction-logs'

export interface StockActualLogRecord {
  id: number
  transaction_time?: string
  transaction_type?: string
  stock_type?: string
  target_cd?: string
  target_name?: string
  quantity?: number
  unit?: string
  location_cd?: string
  process_cd?: string
  process_name?: string
  machine_cd?: string
  machine_name?: string
  related_doc_no?: string
  [key: string]: unknown
}

export interface StockActualStats {
  total_records: number
  total_quantity: number
  avg_quantity: number
  product_count: number
  active_days: number
}

export interface StockActualTypeSummary {
  transaction_type: string
  record_count: number
  total_quantity: number
}

export interface GetStockActualLogsParams {
  page?: number
  limit?: number
  keyword?: string
  date_from?: string
  date_to?: string
  process_cd?: string
  transaction_type?: string
  sort_by?: string
  sort_order?: 'ASC' | 'DESC'
}

/** 生産実績一覧（stats, typeSummary, pagination 付き） */
export async function getStockActualLogs(
  params: GetStockActualLogsParams
): Promise<{
  success?: boolean
  data?: {
    list: StockActualLogRecord[]
    stats: StockActualStats
    typeSummary: StockActualTypeSummary[]
    pagination: { total: number }
  }
  message?: string
}> {
  const res = await request.get(PRODUCTION_ACTUAL_BASE, { params })
  return res as ReturnType<typeof getStockActualLogs> extends Promise<infer R> ? R : never
}

/** 取引ログ 1 件更新 */
export async function updateStockTransactionLog(
  id: number,
  body: Partial<{
    transaction_time: string
    transaction_type: string
    stock_type: string
    target_cd: string
    quantity: number
    location_cd: string
    machine_cd: string
    related_doc_no: string
  }>
): Promise<{ success?: boolean; message?: string }> {
  await request.put(`${STOCK_LOG_BASE}/${id}`, body)
  return { success: true }
}

/** 取引ログ 1 件削除 */
export async function deleteStockTransactionLog(
  id: number
): Promise<{ success?: boolean; message?: string }> {
  await request.delete(`${STOCK_LOG_BASE}/${id}`)
  return { success: true }
}

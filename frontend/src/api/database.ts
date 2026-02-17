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

export interface InventoryShortagePrintParams {
  startDate: string
  endDate: string
  productCd?: string
}

export interface InventoryShortagePrintRow {
  product_cd: string
  product_name: string
  date: string
  destination_name: string
  product_type: string
  box_type: string
  unit_per_box: number | null
  units: number
  box_quantity: number | null
}

/** 在庫不足一覧印刷用（products・destinations ジョイン済み） */
export function getInventoryShortagePrint(params: InventoryShortagePrintParams) {
  return request.get<{ data: InventoryShortagePrintRow[] }>(`${BASE}/inventory-shortage-print`, { params })
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

/** 一括更新用分散ロック取得（他端末同時実行防止） */
export function acquireBatchUpdateLock(lockValue: string, ttlSeconds?: number) {
  return request.post<{ data?: { acquired?: boolean }; message?: string }>(
    `${BASE}/batch-update-lock/acquire`,
    { lockValue, ttlSeconds }
  )
}

/** 一括更新用分散ロック解放 */
export function releaseBatchUpdateLock(lockValue: string) {
  return request.post<{ data?: { released?: boolean }; message?: string }>(
    `${BASE}/batch-update-lock/release`,
    { lockValue }
  )
}

/** 受注データから forecast_quantity / order_quantity を更新 */
export function updateProductionSummarysFromOrderDaily(params?: UpdateFromOrderDailyParams) {
  return request.post(`${BASE}/update-from-order-daily`, params || {})
}

/** 繰越フィールドを全件 0 にクリア */
export function clearProductionSummarysCarryOver() {
  return request.post(`${BASE}/clear-carry-over`)
}

/** 初期在庫ログから繰越を再計算して production_summarys に反映 */
export function updateProductionSummarysCarryOver() {
  return request.post(`${BASE}/update-carry-over`)
}

/** 実績データ更新：stock_transaction_logs から actual 列を再計算して production_summarys に反映 */
export function updateProductionSummarysActual() {
  return request.post<{
    data?: { updated?: number; skipped?: number; cleared?: number; clearPeriod?: string }
    message?: string
  }>(`${BASE}/update-actual`)
}

/** 不良データ更新：stock_transaction_logs の不良を集計して production_summarys の defect 列に反映 */
export function updateProductionSummarysDefect() {
  return request.post<{
    data?: { updated?: number; skipped?: number; total?: number }
    message?: string
  }>(`${BASE}/update-defect`)
}

/** 廃棄データ更新：stock_transaction_logs の廃棄を集計して production_summarys の scrap 列に反映 */
export function updateProductionSummarysScrap() {
  return request.post<{
    data?: { updated?: number; skipped?: number; total?: number }
    message?: string
  }>(`${BASE}/update-scrap`)
}

/** 保留データ更新：stock_transaction_logs の保留を集計して production_summarys の on_hold 列に反映 */
export function updateProductionSummarysOnHold() {
  return request.post<{
    data?: { updated?: number; skipped?: number; total?: number }
    message?: string
  }>(`${BASE}/update-on-hold`)
}

/** 生産計画日更新：product_process_bom のリードタイムで production_summarys の各工程 *_production_date を営業日逆算で更新 */
export function updateProductionSummarysProductionDates() {
  return request.post<{
    data?: { updated?: number; skipped?: number; total?: number }
    message?: string
  }>(`${BASE}/update-production-dates`)
}

/** 計算フィールド（在庫・推移・actual_plan_trend）を date >= startDate で 0 にクリア */
export function clearProductionSummarysCalculatedFields(startDate: string) {
  return request.post<{ message?: string }>(`${BASE}/clear-calculated-fields`, { startDate })
}

/** 計画データ更新：production_plan_updates を集計して production_summarys の plan / actual_plan を更新 */
export function updateProductionSummarysPlan() {
  return request.post<{
    data?: { updated?: number; skipped?: number; total?: number; elapsedTime?: number }
    message?: string
  }>(`${BASE}/update-plan`)
}

/** 在庫・推移更新は処理時間がかかるため 5 分タイムアウト */
const LONG_REQUEST_TIMEOUT = 5 * 60 * 1000

/** 在庫更新：開始日～+3ヶ月の在庫列を再計算 */
export function updateProductionSummarysInventory(startDate?: string) {
  return request.post<{
    data?: { updated?: number; skipped?: number; total?: number; elapsedTime?: number }
    message?: string
  }>(`${BASE}/update-inventory`, startDate != null ? { startDate } : {}, { timeout: LONG_REQUEST_TIMEOUT })
}

/** 推移更新：開始日～+3ヶ月の trend / actual_plan_trend を再計算 */
export function updateProductionSummarysTrend(startDate?: string) {
  return request.post<{
    data?: { updated?: number; skipped?: number; total?: number; elapsedTime?: number }
    message?: string
  }>(`${BASE}/update-trend`, startDate != null ? { startDate } : {}, { timeout: LONG_REQUEST_TIMEOUT })
}

/** 安全在庫更新：将来30営業日の平均内示数×製品マスタsafety_days で safety_stock を再計算 */
export function updateProductionSummarysSafetyStock(startDate?: string) {
  return request.post<{
    data?: { updated?: number; skipped?: number; total?: number; elapsedTime?: number }
    message?: string
  }>(`${BASE}/update-safety-stock`, startDate != null ? { startDate } : {}, { timeout: LONG_REQUEST_TIMEOUT })
}

/** 製品マスタ更新：products の route_cd, product_name を production_summarys に同期 */
export function updateProductionSummarysProductMaster(body: { startDate: string; endDate: string }) {
  return request.post<{
    data?: { updated?: number; skipped?: number; startDate?: string; endDate?: string; elapsedTime?: number }
    message?: string
  }>(`${BASE}/update-product-master`, body)
}

/** 設備フィールド更新：product_machine_config + machines から production_summarys の各 *_machine を同期 */
export function updateProductionSummarysMachine(body: { startDate: string; endDate: string }) {
  return request.post<{
    data?: { updated?: number; skipped?: number; startDate?: string; endDate?: string; elapsedTime?: number }
    message?: string
  }>(`${BASE}/update-machine`, body)
}

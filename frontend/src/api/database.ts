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

/** production_summarys 一覧行（在庫一覧で使用するフィールド） */
export interface ProductionSummaryInventoryRow {
  id?: number
  product_cd: string
  product_name: string | null
  /** メッキ治具（設備マスタ連携） */
  plating_machine?: string | null
  date: string
  day_of_week: string | null
  cutting_inventory?: number | null
  chamfering_inventory?: number | null
  molding_inventory?: number | null
  plating_inventory?: number | null
  welding_inventory?: number | null
  inspection_inventory?: number | null
  warehouse_inventory?: number | null
  outsourced_warehouse_inventory?: number | null
  outsourced_plating_inventory?: number | null
  outsourced_welding_inventory?: number | null
  /** ルート上 溶接/外注溶接 の直前工程の在庫（一覧 enrich と同一） */
  pre_welding_inventory?: number | null
  pre_welding_prev_process?: string | null
  pre_welding_inspection_inventory?: number | null
  pre_inspection_inventory?: number | null
  pre_outsourcing_inventory?: number | null
  /** 社内メッキ(KT05)直前工程在庫（ルート上 plating の一つ手前のみ。外注メッキは対象外） */
  pre_kt05_plating_inventory?: number | null
  pre_kt05_plating_prev_process?: string | null
}

/** 一覧取得（ページネーション） */
export function getProductionSummarysList(params: ProductionSummaryListParams) {
  return request.get(BASE, { params })
}

/** production_summarys を期間集計し、工程別に (不良+廃棄)/実績 を算出 */
export function getQualityRateByProcess(params: {
  startDate: string
  endDate: string
  process?: string
}) {
  return request.get<{
    data: {
      start_date: string
      end_date: string
      process_filter: string | null
      processes: Array<{
        key: string
        label: string
        sum_actual: number
        sum_defect: number
        sum_scrap: number
        sum_defect_and_scrap: number
        rate: number | null
        rate_percent: number | null
      }>
      summary: {
        basis: 'rolled_main_line' | 'selected_process'
        reference_process_key: string
        reference_process_label: string
        sum_actual: number
        sum_defect: number
        sum_scrap: number
        sum_defect_and_scrap: number
        rate: number | null
        rate_percent: number | null
        rolled_yield_rate: number | null
        rolled_yield_percent: number | null
      }
      /** 全工程の不良＋廃棄数量の単純合計（期間内・工程フィルタとは独立） */
      all_processes_defect_scrap_total: number
    }
  }>(`${BASE}/quality-rate-by-process`, { params })
}

/** 製品別・主ライン（切断～検査）の工程別（不良+廃棄）/実績（GROUP BY product_cd） */
export function getQualityRateByProduct(params: {
  startDate: string
  endDate: string
  page?: number
  limit?: number
  productCd?: string
  keyword?: string
  /** 既定: product_name。all_processes_defect_scrap=全工程不良+廃棄合計。主ライン工程キーは当該工程比率でソート */
  sortBy?: string
  /** asc | desc */
  sortOrder?: 'asc' | 'desc'
}) {
  return request.get<{
    data: {
      start_date: string
      end_date: string
      scope: string
      main_line_labels: Array<{ key: string; label: string }>
      pagination: { total: number; page: number; limit: number }
      products: Array<{
        product_cd: string
        product_name: string
        /** 定義済み全工程の不良＋廃棄（期間内・製品単位） */
        all_processes_defect_scrap: number
        processes: Array<{
          key: string
          label: string
          sum_actual: number
          sum_defect: number
          sum_scrap: number
          sum_defect_and_scrap: number
          rate: number | null
          rate_percent: number | null
        }>
      }>
    }
  }>(`${BASE}/quality-rate-by-product`, { params })
}

/** 製品一覧（重複なし） */
export function getProductionSummarysProducts() {
  return request.get(`${BASE}/products`)
}

/** 在庫停滞（*_inventory 列）検知 */
export interface InventoryStagnationParams {
  /** 基準日 YYYY-MM-DD（省略時: サーバー JST 当日） */
  as_of?: string
  /** この値より大きい同一在庫値のみを対象（既定 50） */
  min_quantity?: number
  /** 連続同一値と判定する暦日数（既定 7） */
  stable_calendar_days?: number
  productCd?: string
  keyword?: string
}

export interface InventoryStagnationRow {
  product_cd: string
  product_name: string
  route_cd: string
  inventory_column: string
  stable_quantity: number
  period_start: string
  period_end: string
  days: number
}

export interface InventoryStagnationResponse {
  data: {
    list: InventoryStagnationRow[]
    total: number
    as_of: string
    period_start: string
    period_end: string
    min_quantity: number
    stable_calendar_days: number
  }
}

export function getInventoryStagnation(params?: InventoryStagnationParams) {
  return request.get<InventoryStagnationResponse>(`${BASE}/inventory-stagnation`, { params })
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
  inspection_inventory?: number | null
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

/** 実績データ更新：当月（JST）1 日～当月末日の actual を 0 クリア後、stock_transaction_logs から再集計して反映 */
export function updateProductionSummarysActual() {
  return request.post<{
    data?: { updated?: number; skipped?: number; cleared?: number; clearPeriod?: string }
    message?: string
  }>(`${BASE}/update-actual`)
}

/** 不良データ更新：当月（JST）1 日～当月末日の各工程 *_defect を 0 クリア後、stock_transaction_logs の不良を集計して反映 */
export function updateProductionSummarysDefect() {
  return request.post<{
    data?: {
      updated?: number
      skipped?: number
      total?: number
      cleared?: number
      clearPeriod?: string
    }
    message?: string
  }>(`${BASE}/update-defect`)
}

/** 廃棄データ更新：当月（JST）1 日～当月末日の各工程 *_scrap を 0 クリア後、stock_transaction_logs の廃棄を集計して反映 */
export function updateProductionSummarysScrap() {
  return request.post<{
    data?: {
      updated?: number
      skipped?: number
      total?: number
      cleared?: number
      clearPeriod?: string
    }
    message?: string
  }>(`${BASE}/update-scrap`)
}

/** 保留データ更新：当月（JST）1 日～当月末日の各工程 *_on_hold を 0 クリア後、stock_transaction_logs の保留を集計して反映 */
export function updateProductionSummarysOnHold() {
  return request.post<{
    data?: {
      updated?: number
      skipped?: number
      total?: number
      cleared?: number
      clearPeriod?: string
    }
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

/** 計画列（_plan / _actual_plan）を date >= startDate ～ +5ヶ月 で 0 にクリア（計画データ更新前初期化用） */
export function clearProductionSummarysPlanFields(startDate: string) {
  return request.post<{ message?: string; data?: { cleared?: number } }>(`${BASE}/clear-plan-fields`, { startDate })
}

/** 成型計画：date >= startDate の行で molding_plan・molding_actual_plan を 0 にクリア（終了日なし） */
export function clearProductionSummarysMoldingPlan(startDate: string) {
  return request.post<{ message?: string; data?: { cleared?: number; startDate?: string } }>(
    `${BASE}/clear-molding-plan`,
    { startDate },
  )
}

/** 計画データ更新：schedule_details.planned_qty を集計（× production_schedules × machines × processes）して各工程 *_plan（溶接は welding_plan）等と actual_plan を更新。startDate 指定時はその日～+5ヶ月のみ対象 */
export function updateProductionSummarysPlan(startDate?: string) {
  return request.post<{
    data?: { updated?: number; skipped?: number; total?: number; elapsedTime?: number }
    message?: string
  }>(`${BASE}/update-plan`, startDate != null ? { startDate } : {})
}

/** 在庫・推移更新は処理時間がかかるため 5 分タイムアウト */
const LONG_REQUEST_TIMEOUT = 5 * 60 * 1000

/** 在庫・推移・安全在庫の計算開始日（初期ログの最新 transaction_time の日付、無ければ当月月初JST） */
export function getInventoryTrendCalcStartDate() {
  return request.get<{
    code?: number
    data?: { startDate?: string; source?: string }
    message?: string
  }>(`${BASE}/inventory-trend-calc-start-date`)
}

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

// ========== 在庫KPI（設計書：production_summarys ベース） ==========
const KPI_BASE = '/api/database/inventory-kpi'

export interface TurnoverRow {
  product_cd: string
  product_name: string
  period_forecast: number
  opening_inventory: number
  closing_inventory: number
  avg_inventory: number
  turnover: number | null
  turnover_days: number | null
}

export function getInventoryTurnover(params: {
  start_date?: string
  end_date?: string
  period_type?: 'month' | 'quarter' | 'year'
  product_cd?: string
  by_amount?: boolean
}) {
  return request.get<{ data: { list: TurnoverRow[]; start_date: string; end_date: string; by_amount: boolean } }>(
    `${KPI_BASE}/turnover`,
    { params }
  )
}

export interface AvgInventoryDaysRow {
  product_cd: string
  product_name: string
  current_inventory: number
  avg_daily_demand: number
  avg_inventory_days: number | null
  latest_date: string | null
}

export function getAvgInventoryDays(params: {
  as_of_date?: string
  recent_days?: number
  product_cd?: string
}) {
  return request.get<{
    data: { list: AvgInventoryDaysRow[]; as_of_date: string; recent_days: number }
  }>(`${KPI_BASE}/avg-inventory-days`, { params })
}

export interface ShortageAlertRow {
  product_cd: string
  product_name: string
  current_inventory: number
  avg_inventory_days: number | null
  lead_time: number
  safety_margin_days: number
  threshold_days: number
}

export function getShortageAlerts(params: {
  as_of_date?: string
  recent_days?: number
  safety_margin_days?: number
  product_cd?: string
}) {
  return request.get<{ data: { list: ShortageAlertRow[]; as_of_date: string } }>(
    `${KPI_BASE}/shortage-alerts`,
    { params }
  )
}

export interface OverstockAlertRow {
  product_cd: string
  product_name: string
  current_inventory: number
  turnover: number | null
  turnover_days: number | null
  last_ship_date: string | null
  days_since_ship: number | null
  over_by_turnover: boolean
  over_by_ship: boolean
}

export function getOverstockAlerts(params: {
  as_of_date?: string
  turnover_period_days?: number
  max_turnover_days?: number
  days_since_ship?: number
  product_cd?: string
}) {
  return request.get<{
    data: {
      list: OverstockAlertRow[]
      as_of_date: string
      max_turnover_days?: number
      days_since_ship?: number
    }
  }>(`${KPI_BASE}/overstock-alerts`, { params })
}

export interface ReorderPointRow {
  product_cd: string
  product_name: string
  latest_date: string | null
  warehouse_inventory: number
  safety_stock: number
  below_reorder: boolean
}

export function getReorderPointList(params: { as_of_date?: string; product_cd?: string }) {
  return request.get<{ data: { list: ReorderPointRow[]; as_of_date: string } }>(
    `${KPI_BASE}/reorder-point`,
    { params }
  )
}

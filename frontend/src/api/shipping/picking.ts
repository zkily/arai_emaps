import request from '@/utils/request'

const PICKING_SYNC_TIMEOUT_MS = 300000

/** ピッキング進捗・本日集計（ShippingPickingHome / ヘッダ通知と同一ソース） */
export function getPickingNewProgress() {
  return request.get('/api/shipping/picking/new-progress')
}

/** 監視フォルダの PickingLog.csv（無ければ Partslog.csv）を shipping_log に取込後、picking_log_matched を全件再計算 */
export function refreshPickingLogMatchedFromLog() {
  return request.post('/api/shipping/items/refresh-picking-log-matched', {}, { timeout: PICKING_SYNC_TIMEOUT_MS })
}

/** 非同期突合タスク起動（即時 task_id を返す） */
export function startRefreshPickingLogMatchedTask() {
  return request.post('/api/shipping/items/refresh-picking-log-matched/async')
}

/** 非同期突合タスク状態取得 */
export function getRefreshPickingLogMatchedTask(taskId: string) {
  return request.get(`/api/shipping/items/refresh-picking-log-matched/tasks/${encodeURIComponent(taskId)}`)
}

// Get picking history data
export function getPickingHistoryData(params: { start_date: string; end_date: string }) {
  return request.get('/api/shipping/picking/history', { params })
}

// Get performance by destination（担当者＝納入先グループ、shipping_items + picking_log_matched で集計）
export function getPerformanceByDestination(params: {
  start_date: string
  end_date: string
  group_names?: string
  page_key?: string
}) {
  return request.get('/api/shipping/picking/performance-by-destination', { params })
}

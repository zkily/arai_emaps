import request from '@/utils/request'

/** 監視フォルダの PickingLog.csv（無ければ Partslog.csv）を shipping_log に取込後、picking_log_matched を全件再計算 */
export function refreshPickingLogMatchedFromLog() {
  return request.post('/api/shipping/items/refresh-picking-log-matched')
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

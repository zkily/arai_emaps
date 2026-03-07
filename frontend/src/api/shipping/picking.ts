import request from '@/utils/request'

// Sync shipping data to picking tasks
export function syncShippingDataToPickingTasks() {
  return request.post('/api/shipping/picking/sync-data')
}

// Get picking history data
export function getPickingHistoryData(params: { start_date: string; end_date: string }) {
  return request.get('/api/shipping/picking/history', { params })
}

// Get performance by destination（担当者＝納入先グループ group_name，按该组 destinations + 日期在 picking_tasks 上汇总）
export function getPerformanceByDestination(params: {
  start_date: string
  end_date: string
  group_names?: string
  page_key?: string
}) {
  return request.get('/api/shipping/picking/performance-by-destination', { params })
}

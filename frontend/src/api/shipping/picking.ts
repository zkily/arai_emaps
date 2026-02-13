import request from '@/utils/request'

// Sync shipping data to picking tasks
export function syncShippingDataToPickingTasks() {
  return request.post('/api/shipping/picking/sync-data')
}

// Get picking history data
export function getPickingHistoryData(params: { start_date: string; end_date: string }) {
  return request.get('/api/shipping/picking/history', { params })
}

// Get performance by destination（可选 picker_names / group_names 用于担当者・グループ分析）
export function getPerformanceByDestination(params: {
  start_date: string
  end_date: string
  picker_names?: string[]
  group_names?: string
}) {
  return request.get('/api/shipping/picking/performance-by-destination', { params })
}

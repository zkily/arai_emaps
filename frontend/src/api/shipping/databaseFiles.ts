import request from '@/utils/request'

const ARCHIVE_TIMEOUT_MS = 300000

export interface ShippingLogRecord {
  id: number
  project: string
  date: string
  datetime: string
  model_no: string
  person_in_charge: string
  picking_no: string
  product_name: string
  product_code: string
  product_name_2: string
  quantity: number
  shipping_quantity: number
  created_at: string
  updated_at: string
}

export interface DuplicateStats {
  total_duplicates: number
  unique_picking_nos: number
  details: Array<{ picking_no: string; product_code: string; count: number }>
}

export interface ArchiveTask {
  task_id: string
  status: 'queued' | 'running' | 'completed' | 'failed' | string
  progress_percent: number
  message?: string
  archived?: number
  total_candidates?: number
  retention_days?: number
  error?: string | null
}

export function getShippingLogs(params?: { page?: number; pageSize?: number; search?: string }) {
  return request.get('/api/shipping/picking/shipping-logs', { params })
}

export function startArchiveShippingLogs() {
  return request.post('/api/shipping/picking/cleanup-logs/async')
}

export function getArchiveShippingLogsTask(taskId: string) {
  return request.get(
    `/api/shipping/picking/cleanup-logs/tasks/${encodeURIComponent(taskId)}`,
  )
}

/** 互換用：同期アーカイブ（進捗なし） */
export function cleanupShippingLogs() {
  return request.post('/api/shipping/picking/cleanup-logs', {}, { timeout: ARCHIVE_TIMEOUT_MS })
}

export function getDuplicateStats(): Promise<DuplicateStats> {
  return request.get('/api/shipping/picking/duplicate-stats')
}

export function performDeduplicate() {
  return request.post('/api/shipping/picking/deduplicate')
}

export function getSyncDebugInfo() {
  return request.get('/api/shipping/picking/sync-debug')
}

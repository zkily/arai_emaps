import request from '@/utils/request'

export interface FileWatcherStatus {
  isRunning: boolean
  watchPath: string
  lastProcessTime: string | null
  processedFiles: number
}

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

const BASE = '/api/system/settings'

export function getFileWatcherStatus(): Promise<FileWatcherStatus> {
  return request.get(`${BASE}/file-watcher`).then((r: any) => ({
    isRunning: r?.isRunning ?? false,
    watchPath: r?.watchPath ?? '',
    lastProcessTime: r?.lastProcessTime ?? null,
    processedFiles: r?.processedFiles ?? 0,
  }))
}

export function startFileWatcher() {
  return request.post(`${BASE}/file-watcher/start`)
}

export function stopFileWatcher() {
  return request.post(`${BASE}/file-watcher/stop`)
}

export function processFile(filename: string) {
  return request.post(`${BASE}/file-watcher/process`, { filename })
}

export function getShippingLogs(params?: { page?: number; pageSize?: number; search?: string }) {
  return request.get('/api/shipping/picking/shipping-logs', { params })
}

export function cleanupShippingLogs() {
  return request.post('/api/shipping/picking/cleanup-logs')
}

export function getDuplicateStats(): Promise<DuplicateStats> {
  return request.get('/api/shipping/picking/duplicate-stats')
}

export function performDeduplicate() {
  return request.post('/api/shipping/picking/deduplicate')
}

export function syncToPickingTasks() {
  return request.post('/api/shipping/picking/sync-data')
}

export function getSyncStatus() {
  return request.get('/api/shipping/picking/sync-status')
}

export function createPickingTable() {
  return request.post('/api/shipping/picking/db/init')
}

export function getSyncDebugInfo() {
  return request.get('/api/shipping/picking/sync-debug')
}

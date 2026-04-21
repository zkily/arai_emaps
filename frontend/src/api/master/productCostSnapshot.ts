/**
 * 累計単価スナップショット / 一括再計算 API
 */
import request from '@/shared/api/request'

export interface CumulativeSnapshotRow {
  row_kind: 'route_step' | 'unassigned'
  row_order: number
  step_no: number | null
  process_cd: string | null
  stage_label: string
  material_increment: number
  part_increment: number
  process_increment: number
  stage_increment: number
  cumulative_unit_price: number
}

export interface CumulativeSnapshotDetail {
  snapshot_id: string
  product_cd: string
  route_cd: string
  bom_header_id: number | null
  created_at?: string | null
  created_by?: string | null
  rows: CumulativeSnapshotRow[]
  errors?: string[]
}

export interface CumulativeSnapshotSummary {
  snapshot_id: string
  product_cd: string
  route_cd: string
  bom_header_id: number | null
  created_at: string | null
  created_by: string | null
  is_latest: number
  cumulative_unit_price_final: number
  row_count: number
}

export type SnapshotMode = 'append_snapshot' | 'replace_current'

export interface RecalcItem {
  product_cd: string
  route_cd?: string | null
  bom_header_id?: number | null
}

export interface RecalcJobStatus {
  id: number
  status: 'queued' | 'running' | 'completed' | 'failed' | 'partial'
  mode: SnapshotMode
  scope: 'selected' | 'all'
  total_items: number
  done_items: number
  success_items: number
  failed_items: number
  progress_percent: number
  message: string | null
  errors: Array<{ product_cd: string; route_cd?: string | null; error: string }>
  result_snapshot_ids: string[]
  created_at: string | null
  started_at: string | null
  finished_at: string | null
  payload?: Record<string, unknown>
}

const BASE = '/api/master/product-cost-snapshots'

export function previewCumulative(params: {
  product_cd: string
  route_cd?: string
  bom_header_id?: number
}) {
  return request.get(`${BASE}/preview`, { params }) as Promise<{
    success: boolean
    data: {
      product_cd: string
      route_cd: string
      bom_header_id: number | null
      rows: CumulativeSnapshotRow[]
      errors: string[]
    }
  }>
}

export function saveCumulativeSnapshot(payload: {
  product_cd: string
  route_cd?: string
  bom_header_id?: number
  mode?: SnapshotMode
  remarks?: string
}) {
  return request.post(BASE, payload) as Promise<{
    success: boolean
    data: {
      snapshot_id: string
      product_cd: string
      route_cd: string
      bom_header_id: number | null
      rows: CumulativeSnapshotRow[]
      errors: string[]
    }
  }>
}

export function listCumulativeSnapshots(params: {
  product_cd?: string
  route_cd?: string
  page?: number
  limit?: number
}) {
  return request.get(BASE, { params }) as Promise<{
    success: boolean
    data: { list: CumulativeSnapshotSummary[]; total: number }
  }>
}

export function getLatestCumulativeSnapshot(params: { product_cd: string; route_cd: string }) {
  return request.get(`${BASE}/latest`, { params }) as Promise<{
    success: boolean
    data: CumulativeSnapshotDetail | null
  }>
}

export function getCumulativeSnapshotDetail(snapshotId: string) {
  return request.get(`${BASE}/${encodeURIComponent(snapshotId)}`) as Promise<{
    success: boolean
    data: CumulativeSnapshotDetail
  }>
}

export function startRecalcJob(body: {
  scope: 'selected' | 'all'
  items?: RecalcItem[]
  mode?: SnapshotMode
}) {
  return request.post(`${BASE}/recalc`, body) as Promise<{
    success: boolean
    data: { job_id: number; status: string; total_items: number }
  }>
}

export function getRecalcJob(jobId: number) {
  return request.get(`${BASE}/recalc/${jobId}`) as Promise<{
    success: boolean
    data: RecalcJobStatus
  }>
}

export function listRecalcJobs(params: { page?: number; limit?: number; status?: string }) {
  return request.get(`${BASE}/recalc`, { params }) as Promise<{
    success: boolean
    data: { list: RecalcJobStatus[]; total: number }
  }>
}

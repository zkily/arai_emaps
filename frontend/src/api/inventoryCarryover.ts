/**
 * 棚卸繰越 API（production_summarys：月末 *_inventory プレビュー・翌月繰越反映）
 */
import request from '@/shared/api/request'

const BASE = '/api/database/production-summarys'

export interface CarryoverPreviewRow {
  product_cd: string
  product_name: string
  item: string
  total_quantity: number
  unit: string
  location_cd: string
}

export interface CarryoverPreviewPayload {
  list: CarryoverPreviewRow[]
  total: number
  page: number
  pageSize: number
  total_quantity_sum: number
}

export interface CarryoverPreviewResponse {
  data: CarryoverPreviewPayload
  as_of_date?: string
  inventory_column?: string
  process_cd?: string
}

const DEFAULT_PAGE_SIZE = 20

export async function getCarryoverData(params: {
  month: string
  process_cd: string
  page?: number
  pageSize?: number
}): Promise<CarryoverPreviewPayload> {
  const res = (await request.get<CarryoverPreviewResponse>(`${BASE}/stocktake-carryover-preview`, {
    params: {
      month: params.month,
      process_cd: params.process_cd,
      page: params.page ?? 1,
      pageSize: params.pageSize ?? DEFAULT_PAGE_SIZE,
    },
  })) as unknown as CarryoverPreviewResponse
  const d = res?.data
  if (d && Array.isArray(d.list)) {
    return {
      list: d.list,
      total: d.total ?? 0,
      page: d.page ?? 1,
      pageSize: d.pageSize ?? DEFAULT_PAGE_SIZE,
      total_quantity_sum: d.total_quantity_sum ?? 0,
    }
  }
  return {
    list: [],
    total: 0,
    page: 1,
    pageSize: DEFAULT_PAGE_SIZE,
    total_quantity_sum: 0,
  }
}

export interface CarryoverExecuteResponse {
  data?: { successCount: number; skippedCount?: number }
  message?: string
}

export interface CarryoverExecuteResult {
  successCount: number
  skippedCount?: number
}

export async function executeCarryover(params: {
  month: string
  process_cd: string
  selectedData: Array<{ product_cd: string; total_quantity: number }>
}): Promise<CarryoverExecuteResult> {
  const res = (await request.post<CarryoverExecuteResponse>(
    `${BASE}/stocktake-carryover-execute`,
    params,
  )) as unknown as CarryoverExecuteResponse
  return res?.data ?? { successCount: 0, skippedCount: 0 }
}

export interface CarryoverProcessSummary {
  process_cd: string
  process_name: string
  inventory_column: string
  count: number
  total_quantity: number
  carried_count: number
}

export interface CarryoverSummaryPayload {
  month: string
  as_of_date: string
  target_date: string
  processes: CarryoverProcessSummary[]
}

/** 対象月の全工程の繰越対象件数・数量・繰越済み件数 */
export async function getCarryoverSummary(month: string): Promise<CarryoverSummaryPayload> {
  const res = (await request.get(`${BASE}/stocktake-carryover-summary`, {
    params: { month },
  })) as unknown as { data?: CarryoverSummaryPayload }
  return (
    res?.data ?? { month, as_of_date: '', target_date: '', processes: [] }
  )
}

export interface CarryoverExecuteAllResult {
  successCount: number
  skippedCount: number
  existingCount: number
  totalQuantity: number
  processes: Array<{
    process_cd: string
    process_name: string
    successCount: number
    skippedCount: number
    existingCount: number
    quantity: number
  }>
}

/** 対象月の全工程を一括繰越（既定で繰越済みはスキップ） */
export async function executeCarryoverAll(params: {
  month: string
  skip_existing?: boolean
}): Promise<CarryoverExecuteAllResult> {
  const res = (await request.post(`${BASE}/stocktake-carryover-execute-all`, {
    month: params.month,
    skip_existing: params.skip_existing ?? true,
  })) as unknown as { data?: CarryoverExecuteAllResult }
  return (
    res?.data ?? {
      successCount: 0,
      skippedCount: 0,
      existingCount: 0,
      totalQuantity: 0,
      processes: [],
    }
  )
}

export async function getCarryoverHistory(params: {
  page?: number
  pageSize?: number
  [key: string]: unknown
}) {
  return {
    list: [],
    total: 0,
    page: params.page ?? 1,
    pageSize: params.pageSize ?? 20,
  }
}

export async function deleteCarryoverRecord(_id: number) {
  return { ok: true }
}

export async function addCarryoverRecord(_data: unknown) {
  return { ok: true }
}

export async function updateCarryoverRecord(_id: number, _data: unknown) {
  return { ok: true }
}

export async function exportCarryoverHistory(_params: unknown) {
  return { data: '' }
}

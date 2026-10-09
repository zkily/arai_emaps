/**
 * 設備能率管理 API
 */
import request from '@/shared/api/request'

export interface EquipmentEfficiency {
  id?: number
  machine_cd?: string
  machines_name?: string
  product_cd?: string
  product_name?: string
  efficiency_rate?: number
  current_efficiency_rate?: number | null
  current_efficiency_updated_at?: string | null
  step_time?: number
  unit?: string
  remarks?: string
  status?: number
  created_at?: string
  updated_at?: string
}

export interface EquipmentEfficiencyTabCounts {
  all: number
  cutting: number
  chamfering: number
  forming: number
  welding: number
  plating: number
  inspection: number
  other: number
}

export interface EquipmentEfficiencyListParams {
  keyword?: string
  /** 互換: 指定時は従来どおり先頭から最大 limit 件（ページングなし） */
  limit?: number
  page?: number
  pageSize?: number
  /** all / cutting / chamfering / …（バックエンドの工程 CASE と一致） */
  processType?: string
  machineCd?: string
  productCd?: string
}

export interface EquipmentEfficiencyFilterPair {
  machine_cd?: string | null
  machines_name?: string | null
  product_cd?: string | null
  product_name?: string | null
  process_type?: string
}

/** 絞込プルダウン用（登録済みの設備×製品の組み合わせ） */
export function fetchEquipmentEfficiencyFilterOptions(): Promise<{
  success?: boolean
  data?: { pairs: EquipmentEfficiencyFilterPair[] }
}> {
  return request.get(`${BASE}/filter-options`) as Promise<{
    success?: boolean
    data?: { pairs: EquipmentEfficiencyFilterPair[] }
  }>
}

export interface EquipmentEfficiencyListResponse {
  success?: boolean
  data?: {
    list: EquipmentEfficiency[]
    total: number
    tab_counts?: EquipmentEfficiencyTabCounts
    machine_distinct_count?: number
    product_distinct_count?: number
  }
  list?: EquipmentEfficiency[]
  total?: number
  tab_counts?: EquipmentEfficiencyTabCounts
  machine_distinct_count?: number
  product_distinct_count?: number
}

const BASE = '/api/master/equipment-efficiency'

export function fetchEquipmentEfficiencyList(
  params?: EquipmentEfficiencyListParams
): Promise<EquipmentEfficiencyListResponse> {
  return request.get(BASE, { params }) as Promise<EquipmentEfficiencyListResponse>
}

export interface EquipmentEfficiencyMaterial {
  material_cd: string
  material_name: string
}

export interface EquipmentEfficiencyByProcessRow extends EquipmentEfficiency {
  process_type?: string
  materials?: EquipmentEfficiencyMaterial[]
}

export interface EquipmentEfficiencyByProcessParams {
  keyword?: string
  processType?: string
}

/** 工程別一覧（設備ごとの製品・能率・使用材料） */
export function fetchEquipmentEfficiencyByProcess(
  params?: EquipmentEfficiencyByProcessParams
): Promise<{ success?: boolean; data?: { list: EquipmentEfficiencyByProcessRow[]; total: number } }> {
  return request.get(`${BASE}/by-process`, { params }) as Promise<{
    success?: boolean
    data?: { list: EquipmentEfficiencyByProcessRow[]; total: number }
  }>
}

export function getEquipmentEfficiencyById(id: number): Promise<EquipmentEfficiency> {
  return request.get(`${BASE}/${id}`) as Promise<EquipmentEfficiency>
}

export function createEquipmentEfficiency(data: Partial<EquipmentEfficiency>): Promise<EquipmentEfficiency> {
  return request.post(BASE, data) as Promise<EquipmentEfficiency>
}

export function updateEquipmentEfficiency(
  id: number,
  data: Partial<EquipmentEfficiency>
): Promise<EquipmentEfficiency> {
  return request.put(`${BASE}/${id}`, data) as Promise<EquipmentEfficiency>
}

export function deleteEquipmentEfficiency(id: number): Promise<{ message: string }> {
  return request.delete(`${BASE}/${id}`) as Promise<{ message: string }>
}

export interface CurrentEfficiencyRefreshResult {
  period_from: string
  period_to: string
  factor: number
  updated: number
  cleared: number
  skipped: number
  sources: string[]
  sources_skipped: string[]
  excluded_processes: string[]
}

/** 直近3ヶ月の生産性から現在能率を一括更新（能率は変えない） */
export function refreshEquipmentCurrentEfficiency(): Promise<CurrentEfficiencyRefreshResult> {
  return request.post(`${BASE}/refresh-current-rate`) as Promise<CurrentEfficiencyRefreshResult>
}

export interface ProductivityMissingCandidate {
  process: string
  machine_cd: string
  machines_name: string
  product_cd: string
  product_name: string
  actual_qty: number
  work_hours: number
  record_count: number
  efficiency_rate: number
}

export interface ProductivityMissingResult {
  period_from: string
  period_to: string
  factor: number
  sources: string[]
  sources_skipped: string[]
  excluded_processes: string[]
  candidates: ProductivityMissingCandidate[]
  unknown_product_cds: string[]
  unmatched_lines: { process: string; line_name: string; product_count: number }[]
}

/** 生産性（直近3ヶ月）にあって未登録の 設備×製品 */
export function fetchProductivityMissing(): Promise<ProductivityMissingResult> {
  return request.get(`${BASE}/productivity-missing`) as Promise<ProductivityMissingResult>
}

/** 未登録の組み合わせを追加（能率＝現在能率） */
export function addProductivityMissing(
  items: { machine_cd: string; product_cd: string }[]
): Promise<{ period_from: string; period_to: string; added: number }> {
  return request.post(`${BASE}/productivity-missing/add`, { items }) as Promise<{
    period_from: string
    period_to: string
    added: number
  }>
}

/** 現在能率を能率へ反映 */
export function applyEquipmentCurrentEfficiency(id: number): Promise<EquipmentEfficiency> {
  return request.post(`${BASE}/${id}/apply-current-rate`) as Promise<EquipmentEfficiency>
}

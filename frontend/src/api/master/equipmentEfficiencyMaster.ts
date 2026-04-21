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

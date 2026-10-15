import request from '@/shared/api/request'
import type { Judgment } from '@/views/erp/production/equipmentCapacity/capacityCalc'

export interface CapacitySummary {
  item_count: number
  active_count: number
  total_hours: number
  daily_available: number
  production_hours: number
  operating_hours: number
  occupied_hours: number
  occupancy_pct: number | null
  remain_hours: number
  daily_judgment: Judgment
  month_judgment: Judgment
  peak_hourly: number
}

export interface EquipmentListItem {
  id: number
  machine_cd: string
  machine_name: string
  regular_hours: number
  shift_count: number
  overtime_hours: number
  working_days: number
  summary: CapacitySummary
}

export interface EquipmentSuggestion {
  machine_cd: string
  machine_name: string
  source: 'machines' | 'efficiency' | 'both' | string
  product_count: number
}

export interface CapacityItem {
  id?: number
  line_no?: number
  part_no: string
  part_name: string
  monthly_qty: number
  qty_days: number
  rate_per_hour: number
  availability_pct: number
  pass_rate_pct: number
  setup_hours: number
  actual_days: number
  reference_rate: number | null
  current_rate: number | null
  takt1_date: string | null
  takt1_ct: number | null
  takt1_inspect: string
  takt1_prep: string
  takt1_overall: string
  takt2_date: string | null
  takt2_ct: number | null
  takt2_inspect: string
  takt2_prep: string
  takt2_overall: string
  remarks: string
}

export interface EquipmentDetail {
  id: number
  process_cd: string
  process_name: string
  machine_cd: string
  machine_name: string
  regular_hours: number
  shift_count: number
  overtime_hours: number
  working_days: number
  note: string
  daily_available: number
  total_hours: number
  machine_availability_pct?: number
  items: CapacityItem[]
  summary: CapacitySummary
}

export interface CapacityListData {
  process_cd: string
  process_name: string
  equipments: EquipmentListItem[]
  suggestions: EquipmentSuggestion[]
}

const base = '/api/erp/production-equipment-capacity'

export function fetchEquipmentCapacity(process: string) {
  return request.get(`${base}/${process}`) as Promise<{ success: boolean; data: CapacityListData }>
}

export function fetchEquipmentCapacityDetail(process: string, id: number) {
  return request.get(`${base}/${process}/${id}`) as Promise<{ success: boolean; data: EquipmentDetail }>
}

export function createEquipmentCapacity(process: string, body: Record<string, unknown>) {
  return request.post(`${base}/${process}`, body) as Promise<{ success: boolean; data: EquipmentDetail }>
}

export function saveEquipmentCapacity(process: string, id: number, body: Record<string, unknown>) {
  return request.put(`${base}/${process}/${id}`, body) as Promise<{ success: boolean; data: EquipmentDetail }>
}

export function deleteEquipmentCapacity(process: string, id: number) {
  return request.delete(`${base}/${process}/${id}`) as Promise<{ success: boolean }>
}

export function importEquipmentCapacityMaster(
  process: string,
  body: { machines: { machine_cd: string; machine_name: string }[]; with_products: boolean },
) {
  return request.post(`${base}/${process}/import-master`, body) as Promise<{
    success: boolean
    data: { created_ids: number[]; skipped: string[] }
  }>
}

export function importEquipmentCapacityRates(process: string, id: number) {
  return request.post(`${base}/${process}/${id}/import-rates`) as Promise<{
    success: boolean
    data: EquipmentDetail
    meta?: { added: number; updated: number }
  }>
}

export function refreshEquipmentCapacityMetrics(process: string, id: number) {
  return request.post(`${base}/${process}/${id}/refresh-metrics`) as Promise<{
    success: boolean
    data: EquipmentDetail
    meta?: { availability_pct?: number; period?: { start: string; end: string } }
  }>
}

export interface ForecastMonthlyItem {
  product_cd: string
  product_name: string
  monthly_qty: number
}

export function fetchEquipmentCapacityForecastMonthly(process: string, year: number, month: number) {
  return request.get(`${base}/${process}/forecast-monthly`, {
    params: { year, month },
  }) as Promise<{
    success: boolean
    data: {
      year: number
      month: number
      item_count: number
      total_qty: number
      items: ForecastMonthlyItem[]
    }
  }>
}

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

export interface EquipmentEfficiencyListParams {
  keyword?: string
  limit?: number
}

const BASE = '/api/master/equipment-efficiency'

export function fetchEquipmentEfficiencyList(
  params?: EquipmentEfficiencyListParams
): Promise<{ success?: boolean; data?: { list: EquipmentEfficiency[]; total: number }; list?: EquipmentEfficiency[]; total?: number }> {
  return request.get(BASE, { params }) as Promise<any>
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

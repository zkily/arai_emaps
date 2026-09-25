import request from '@/shared/api/request'

const BASE = '/api/quality/equipment-maintenance'

export type ProcessCode = 'cutting' | 'chamfering' | 'forming' | 'welding' | 'plating'
export type WorkType = 'maintenance' | 'repair'
export type RecordStatus = 'planned' | 'done' | 'cancelled'

export interface MaintenanceEquipment {
  id: number
  process_code: ProcessCode
  machine_cd: string | null
  equipment_name: string
  asset_no: string | null
  location: string | null
  cycle_days: number | null
  note: string | null
  is_active: boolean
  sort_order: number
  last_maintenance_date: string | null
  last_repair_date: string | null
  next_planned_date: string | null
  open_plan_count: number
  undetermined_plan_count?: number
  created_by: string | null
  updated_by: string | null
  created_at: string | null
  updated_at: string | null
}

export interface MaintenanceRecord {
  id: number
  equipment_id: number
  process_code: ProcessCode
  equipment_name: string
  machine_cd: string | null
  work_type: WorkType
  status: RecordStatus
  planned_date: string | null
  actual_date: string | null
  title: string | null
  content: string | null
  assignee: string | null
  work_hours: number | null
  note: string | null
  created_by: string | null
  updated_by: string | null
  created_at: string | null
  updated_at: string | null
}

export interface EquipmentPayload {
  process_code: ProcessCode
  machine_cd?: string | null
  equipment_name: string
  asset_no?: string | null
  location?: string | null
  cycle_days?: number | null
  note?: string | null
  is_active?: boolean
  sort_order?: number
}

export interface RecordPayload {
  equipment_id: number
  work_type: WorkType
  status: RecordStatus
  planned_date?: string | null
  actual_date?: string | null
  title?: string | null
  content?: string | null
  assignee?: string | null
  work_hours?: number | null
  note?: string | null
}

interface ListResponse<T> {
  success?: boolean
  data?: { list?: T[]; total?: number }
  message?: string
}

export function fetchMaintenanceEquipments(params: {
  process_code?: string
  keyword?: string
  include_inactive?: boolean
  auto_sync?: boolean
} = {}) {
  return request.get(`${BASE}/equipments`, { params }) as Promise<
    ListResponse<MaintenanceEquipment> & { data?: { list?: MaintenanceEquipment[]; total?: number; synced?: number } }
  >
}

export function createMaintenanceEquipment(data: EquipmentPayload) {
  return request.post(`${BASE}/equipments`, data) as Promise<{ success?: boolean; message?: string }>
}

export function updateMaintenanceEquipment(id: number, data: EquipmentPayload) {
  return request.put(`${BASE}/equipments/${id}`, data) as Promise<{ success?: boolean; message?: string }>
}

export function deleteMaintenanceEquipment(id: number) {
  return request.delete(`${BASE}/equipments/${id}`) as Promise<{ success?: boolean; message?: string }>
}

export function importMaintenanceMachines(process_code?: string) {
  return request.post(`${BASE}/equipments/import-machines`, { process_code: process_code || null }) as Promise<{
    success?: boolean
    message?: string
    data?: { inserted?: number }
  }>
}

export function fetchMaintenanceRecords(params: {
  equipment_id?: number
  process_code?: string
  status?: string
  work_type?: string
  from_date?: string
  to_date?: string
} = {}) {
  return request.get(`${BASE}/records`, { params }) as Promise<ListResponse<MaintenanceRecord>>
}

export function createMaintenanceRecord(data: RecordPayload) {
  return request.post(`${BASE}/records`, data) as Promise<{ success?: boolean; message?: string }>
}

export function updateMaintenanceRecord(id: number, data: RecordPayload) {
  return request.put(`${BASE}/records/${id}`, data) as Promise<{ success?: boolean; message?: string }>
}

export function deleteMaintenanceRecord(id: number) {
  return request.delete(`${BASE}/records/${id}`) as Promise<{ success?: boolean; message?: string }>
}

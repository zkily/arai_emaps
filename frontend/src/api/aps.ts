/**
 * APS 排産スケジューリング API
 */
import request from '@/shared/api/request'

const BASE = '/api/aps'

// ──────────── Types ────────────

export interface ProductionLine {
  id: number
  line_code: string
  default_work_hours: number
  is_active: boolean
}

export interface LineCapacity {
  id: number
  line_id: number
  work_date: string
  available_hours: number
  note?: string | null
}

export interface LineCapacityItem {
  line_id: number
  work_date: string
  available_hours: number
  note?: string | null
}

export interface ScheduleCreateBody {
  line_id: number
  order_no?: number | null
  order_id?: number | null
  item_name: string
  material_shortage?: boolean
  lot_qty?: number
  planned_process_qty: number
  prev_month_carryover?: number
  due_date?: string | null
  material_date?: string | null
  setup_time?: number
  efficiency?: number
  daily_capacity: number
  start_date?: string | null
  run_immediately?: boolean
}

export interface ScheduleUpdateBody {
  line_id?: number | null
  order_no?: number | null
  order_id?: number | null
  item_name?: string | null
  material_shortage?: boolean | null
  lot_qty?: number | null
  planned_process_qty?: number | null
  prev_month_carryover?: number | null
  due_date?: string | null
  material_date?: string | null
  setup_time?: number | null
  efficiency?: number | null
  daily_capacity?: number | null
  start_date?: string | null
  run_immediately?: boolean
}

export interface ScheduleOut {
  id: number
  line_id: number
  order_no?: number | null
  order_id?: number | null
  item_name: string
  material_shortage: boolean
  lot_qty: number
  planned_process_qty: number
  prev_month_carryover: number
  due_date?: string | null
  material_date?: string | null
  setup_time: number
  efficiency: number
  daily_capacity: number
  planned_output_qty: number
  start_date?: string | null
  end_date?: string | null
  completion_rate?: number | null
  status: string
}

export interface ScheduleGridRow {
  id: number
  order_no?: number | null
  item_name: string
  material_shortage: boolean
  lot_qty: number
  planned_process_qty: number
  prev_month_carryover: number
  due_date?: string | null
  material_date?: string | null
  setup_time: number
  efficiency: number
  daily_capacity: number
  planned_output_qty: number
  start_date?: string | null
  end_date?: string | null
  completion_rate?: number | null
  status: string
  daily: Record<string, number>
}

export interface LineGridBlock {
  line_id: number
  line_code: string
  default_work_hours: number
  calendar: Record<string, number>
  rows: ScheduleGridRow[]
  daily_totals: Record<string, number>
  sum_planned_process_qty: number
  sum_planned_output_qty: number
  completion_rate?: number | null
}

export interface SchedulingGridResponse {
  dates: string[]
  blocks: LineGridBlock[]
}

// ──────────── API calls ────────────

export function fetchLines(): Promise<ProductionLine[]> {
  return request.get(`${BASE}/lines`)
}

export function createLine(lineCode: string, defaultWorkHours = 0): Promise<any> {
  return request.post(`${BASE}/lines`, null, {
    params: { line_code: lineCode, default_work_hours: defaultWorkHours },
  })
}

export function fetchLineCapacities(
  lineId: number,
  startDate: string,
  endDate: string,
): Promise<LineCapacity[]> {
  return request.get(`${BASE}/line-capacities`, {
    params: { lineId, startDate, endDate },
  })
}

export function batchUpsertLineCapacities(items: LineCapacityItem[]): Promise<any> {
  return request.post(`${BASE}/line-capacities/batch`, { items })
}

export function fetchSchedules(params?: {
  lineId?: number
  status?: string
}): Promise<ScheduleOut[]> {
  return request.get(`${BASE}/schedules`, { params })
}

export function createSchedule(body: ScheduleCreateBody): Promise<ScheduleOut> {
  return request.post(`${BASE}/schedules`, body)
}

export function updateSchedule(
  scheduleId: number,
  body: ScheduleUpdateBody,
): Promise<ScheduleOut> {
  return request.put(`${BASE}/schedules/${scheduleId}`, body)
}

export function deleteSchedule(scheduleId: number): Promise<any> {
  return request.delete(`${BASE}/schedules/${scheduleId}`)
}

export function runSchedule(scheduleId: number): Promise<any> {
  return request.post(`${BASE}/schedules/${scheduleId}/run`)
}

export function fetchSchedulingGrid(
  startDate: string,
  endDate: string,
  lineId?: number,
): Promise<SchedulingGridResponse> {
  const params: Record<string, any> = { startDate, endDate }
  if (lineId != null) params.lineId = lineId
  return request.get(`${BASE}/scheduling/grid`, { params })
}

export function runAllSchedules(lineId?: number): Promise<any> {
  const params: Record<string, any> = {}
  if (lineId != null) params.lineId = lineId
  return request.post(`${BASE}/run-all`, null, { params })
}

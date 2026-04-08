/**
 * APS 排産スケジューリング API
 */
import request from '@/shared/api/request'

const BASE = '/api/aps'

// ──────────── Types ────────────

export interface ProductionLine {
  id: number
  line_code: string
  /** 設備名（machines.machine_name） */
  line_name?: string
  default_work_hours: number
  is_active: boolean
}

/** 設備プルダウン表示：コード + 設備名 */
export function productionLineOptionLabel(line: ProductionLine): string {
  const name = (line.line_name || '').trim()
  if (name) return `${line.line_code} — ${name}`
  return line.line_code
}

/** equipment_efficiency（APS 品名プルダウン） */
export interface EquipmentEfficiencyProduct {
  id: number
  product_cd: string | null
  product_name: string | null
  efficiency_rate: number
  step_time: number | null
  /** products.lot_size（製品マスタ、product_cd 一致時） */
  lot_size?: number | null
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
  product_cd?: string | null
  material_shortage?: boolean
  lot_qty?: number
  planned_batch_count?: number
  lot_size_snapshot?: number
  planned_process_qty?: number
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
  product_cd?: string | null
  material_shortage?: boolean | null
  lot_qty?: number | null
  planned_batch_count?: number | null
  lot_size_snapshot?: number | null
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
  product_cd?: string | null
  material_shortage: boolean
  lot_qty: number
  planned_batch_count: number
  lot_size_snapshot: number
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
  /** GET /schedules で machines と JOIN 時に付与 */
  line_code?: string
  line_name?: string
}

// ──────────── Time Slots ────────────

export interface TimeSlotItem {
  start_time: string
  end_time: string
  sort_order?: number
  is_rest?: boolean
}

export interface DaySlotsBody {
  line_id: number
  work_date: string
  slots: TimeSlotItem[]
}

export interface TimeSlotOut {
  id: number
  start_time: string
  end_time: string
  sort_order: number
  is_rest?: boolean
}

export interface DaySlotsOut {
  work_date: string
  available_hours: number
  slots: TimeSlotOut[]
}

export interface DaySlotsBatchBody {
  line_id: number
  days: DaySlotsBody[]
}

// ──────────── Line Product Standard ────────────

export interface LineProductStandardBody {
  line_id: number
  product_cd: string
  std_qty_per_hour: number
  setup_time_min?: number
  efficiency_pct?: number
}

export interface LineProductStandardOut {
  id: number
  line_id: number
  product_cd: string
  std_qty_per_hour: number
  setup_time_min: number
  efficiency_pct: number
}

// ──────────── Daily Equipment Report ────────────

export interface DailyEquipmentReportRow {
  schedule_date: string
  line_id: number
  line_code: string
  order_no: number | null
  item_name: string
  product_cd: string | null
  planned_qty: number
  actual_qty: number
  available_hours: number | null
}

export interface ScheduleGridRow {
  id: number
  order_no?: number | null
  item_name: string
  material_shortage: boolean
  lot_qty: number
  planned_batch_count: number
  lot_size_snapshot: number
  planned_process_qty: number
  prev_month_carryover: number
  due_date?: string | null
  material_date?: string | null
  setup_time: number
  efficiency: number
  /** equipment_efficiency 能率（本/H）、ガント表示用 */
  efficiency_rate?: number | null
  daily_capacity: number
  planned_output_qty: number
  start_date?: string | null
  end_date?: string | null
  completion_rate?: number | null
  status: string
  daily: Record<string, number>
  actual_daily?: Record<string, number>
  remaining_daily?: Record<string, number>
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

/** 時間別ガント列・行（schedule_slice_allocations） */
export interface HourlyGridColumn {
  key: string
  work_date: string
  period_start: string
  period_end: string
}

export interface HourlyGridRow {
  schedule_id: number
  order_no?: number | null
  planned_batch_count?: number
  lot_size_snapshot?: number
  planned_process_qty?: number
  /** equipment_efficiency 能率（本/H） */
  efficiency_rate?: number | null
  item_name: string
  slice_qty: Record<string, number>
}

export interface SchedulingHourlyGridResponse {
  columns: HourlyGridColumn[]
  rows: HourlyGridRow[]
}

// ──────────── APS Batch Plans（aps_batch_plans） ────────────
export interface ApsBatchPlanOut {
  id: number
  aps_schedule_id: number
  production_month: string
  production_line: string
  priority_order?: number | null
  product_cd: string
  product_name: string
  planned_quantity: number
  /** 計画一覧確定時の本数（生産進捗の計画数と同趣旨） */
  original_planned_quantity?: number | null
  production_lot_size: number
  lot_number: string
  start_date?: string | null
  end_date?: string | null
  status: string
}

// ──────────── Production Progress（生産進捗） ────────────

export interface ProgressLotItem {
  batch_plan_id: number
  aps_schedule_id: number
  product_cd: string
  product_name: string
  lot_number: string
  planned_quantity: number
  order_no?: number | null
  start_date?: string | null
  end_date?: string | null
  predicted_completion?: string | null
  progress_status: 'PLANNED' | 'RELEASED' | 'IN_PROGRESS' | 'COMPLETED'
  management_code?: string | null
  production_line: string
  /** cutting_management（切断指示）— 生産中ロットのみ */
  cutting_planned_qty?: number | null
  cutting_actual_qty?: number | null
  cutting_completed?: boolean | null
}

/** 生産進捗日別セル：成型の実績・計画（schedule_details）。切断本数は ProgressLotItem.cutting_* */
export type ProgressDailySource = 'ACTUAL' | 'PLANNED' | 'WAIT_UPSTREAM'

export interface ProductionProgressResponse {
  lots: ProgressLotItem[]
  dates: string[]
  lot_daily: Record<string, Record<string, number>>
  lot_daily_source?: Record<string, Record<string, ProgressDailySource>>
}

// ──────────── API calls ────────────

export function fetchLines(processCd?: string | null): Promise<ProductionLine[]> {
  const params: Record<string, string> = {}
  if (processCd != null && String(processCd).trim() !== '') {
    params.processCd = String(processCd).trim()
  }
  return request.get(`${BASE}/lines`, { params: Object.keys(params).length ? params : undefined })
}

export function fetchEquipmentEfficiencyProducts(machineId: number): Promise<EquipmentEfficiencyProduct[]> {
  return request.get(`${BASE}/equipment-efficiency-products`, { params: { machineId } })
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
  processCd?: string
  productionMonth?: string
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
  processCd?: string,
): Promise<SchedulingGridResponse> {
  const params: Record<string, any> = { startDate, endDate }
  if (lineId != null) params.lineId = lineId
  const pc = processCd?.trim()
  if (pc) params.processCd = pc
  return request.get(`${BASE}/scheduling/grid`, { params })
}

export function fetchSchedulingHourlyGrid(
  startDate: string,
  endDate: string,
  lineId: number,
): Promise<SchedulingHourlyGridResponse> {
  return request.get(`${BASE}/scheduling/hourly-grid`, {
    params: { startDate, endDate, lineId },
  })
}

export function fetchApsBatchPlans(params: {
  productionMonth?: string | null
  lineId?: number | null
  productCd?: string | null
}): Promise<ApsBatchPlanOut[]> {
  const p: Record<string, any> = {}
  if (params.productionMonth != null) p.productionMonth = params.productionMonth
  if (params.lineId != null) p.lineId = params.lineId
  if (params.productCd != null) p.productCd = params.productCd
  return request.get(`${BASE}/batch-plans`, { params: p })
}

export function runAllSchedules(lineId?: number, sequential?: boolean): Promise<any> {
  const params: Record<string, any> = {}
  if (lineId != null) params.lineId = lineId
  if (sequential) params.sequential = true
  return request.post(`${BASE}/run-all`, null, { params })
}

export function replanLineSequence(lineId: number, anchorStartDate?: string): Promise<any> {
  const params: Record<string, any> = {}
  if (anchorStartDate) params.anchorStartDate = anchorStartDate
  return request.post(`${BASE}/lines/${lineId}/replan-sequence`, null, { params })
}

// ──────────── Time Slots ────────────

export function fetchLineCapacitySlots(
  lineId: number,
  startDate: string,
  endDate: string,
): Promise<DaySlotsOut[]> {
  return request.get(`${BASE}/line-capacity-slots`, {
    params: { lineId, startDate, endDate },
  })
}

export function batchUpsertLineCapacitySlots(body: DaySlotsBatchBody): Promise<any> {
  return request.put(`${BASE}/line-capacity-slots/batch`, body)
}

// ──────────── Line Product Standard ────────────

export function fetchLineProductStandards(lineId?: number): Promise<LineProductStandardOut[]> {
  const params: Record<string, any> = {}
  if (lineId != null) params.lineId = lineId
  return request.get(`${BASE}/line-product-standards`, { params })
}

export function createLineProductStandard(body: LineProductStandardBody): Promise<LineProductStandardOut> {
  return request.post(`${BASE}/line-product-standards`, body)
}

export function updateLineProductStandard(id: number, body: LineProductStandardBody): Promise<LineProductStandardOut> {
  return request.put(`${BASE}/line-product-standards/${id}`, body)
}

export function deleteLineProductStandard(id: number): Promise<any> {
  return request.delete(`${BASE}/line-product-standards/${id}`)
}

// ──────────── Daily Equipment Report ────────────

export function fetchProductionProgress(lineId: number): Promise<ProductionProgressResponse> {
  return request.get(`${BASE}/production-progress`, { params: { lineId } })
}

export function fetchDailyEquipmentReport(
  startDate: string,
  endDate: string,
  lineId?: number,
): Promise<{ success: boolean; data: DailyEquipmentReportRow[] }> {
  const params: Record<string, any> = { startDate, endDate }
  if (lineId != null) params.lineId = lineId
  return request.get(`${BASE}/daily-equipment-report`, { params })
}

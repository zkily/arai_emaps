import request from '@/shared/api/request'

const BASE = '/api/cutting-planning'

export interface CuttingPlanningMachine {
  id: number
  machine_cd: string
  machine_name: string
  default_work_hours?: number | null
}

export interface CuttingPlanningItem {
  id: number | null
  instruction_plan_id?: number | null
  product_cd: string
  product_name: string
  material_name?: string | null
  production_line?: string | null
  planned_quantity: number
  /** instruction_plans.actual_production_quantity（生産数） */
  instruction_production_quantity: number
  production_lot_size?: number | null
  lot_number?: string | null
  take_count?: number | null
  cutting_length?: number | null
  assigned_machine_id?: number | null
  assigned_machine?: string | null
  sequence_no: number
  planned_day?: string | null
  planned_start?: string | null
  planned_end?: string | null
  estimated_minutes: number
  efficiency_rate?: number | null
  setup_time_min?: number | null
  is_locked: boolean
  publish_status: string
  published_cutting_id?: number | null
  actual_quantity: number
  completion_status: string
  source_management_code?: string | null
}

export interface CuttingPlanningSummary {
  total_items: number
  planned_items: number
  published_items: number
  in_progress_items: number
  completed_items: number
  total_planned_quantity: number
  total_instruction_production_quantity: number
  total_actual_quantity: number
}

export interface CuttingPlanningListResponse {
  run_id: number | null
  generated_at?: string | null
  published_at?: string | null
  machines: CuttingPlanningMachine[]
  items: CuttingPlanningItem[]
  summary: CuttingPlanningSummary
}

export interface CuttingPlanningDailyRow {
  item_id: number
  sequence_no: number
  product_name: string
  product_cd: string
  planned_quantity: number
  daily: Record<string, number>
}

export interface CuttingPlanningDailyBlock {
  machine_id: number
  machine_name: string
  rows: CuttingPlanningDailyRow[]
  daily_totals: Record<string, number>
}

export interface CuttingPlanningGanttResponse {
  dates: string[]
  blocks: CuttingPlanningDailyBlock[]
}

export interface CuttingPlanningHourlyColumn {
  key: string
  work_date: string
  period_start: string
  period_end: string
}

export interface CuttingPlanningHourlyRow {
  item_id: number
  sequence_no: number
  product_name: string
  product_cd: string
  planned_quantity: number
  slice_qty: Record<string, number>
}

export interface CuttingPlanningHourlyResponse {
  columns: CuttingPlanningHourlyColumn[]
  rows: CuttingPlanningHourlyRow[]
}

export interface CuttingPlanningProgressResponse extends CuttingPlanningSummary {
  production_month: string
  run_id?: number | null
}

export interface CuttingPlanningReportItem {
  machine_name?: string | null
  planned_day?: string | null
  sequence_no: number
  product_cd: string
  product_name: string
  material_name?: string | null
  planned_quantity: number
  instruction_production_quantity: number
  estimated_minutes: number
  publish_status: string
  completion_status: string
}

export interface CuttingPlanningReportResponse {
  production_month: string
  generated_at?: string | null
  items: CuttingPlanningReportItem[]
}

export function fetchCuttingPlanningMachines(): Promise<CuttingPlanningMachine[]> {
  return request.get(`${BASE}/machines`)
}

export function fetchCuttingPlanningList(params: {
  productionMonth: string
  machineId?: number | null
  status?: string | null
  keyword?: string | null
}): Promise<CuttingPlanningListResponse> {
  return request.get(`${BASE}/list`, { params })
}

export function syncCuttingPlanFromInstructions(body: {
  production_month: string
}): Promise<CuttingPlanningListResponse> {
  return request.post(`${BASE}/sync-from-instructions`, body)
}

export function scheduleCuttingPlanSelected(body: {
  production_month: string
  run_id: number
  item_ids: number[]
  machine_ids?: number[] | null
  start_date?: string | null
  horizon_days?: number
}): Promise<CuttingPlanningListResponse> {
  return request.post(`${BASE}/schedule-selected`, body)
}

export function autoScheduleCuttingPlans(body: {
  production_month: string
  machine_ids?: number[] | null
  start_date?: string | null
  horizon_days?: number
  preserve_published?: boolean
}): Promise<CuttingPlanningListResponse> {
  return request.post(`${BASE}/auto-schedule`, body)
}

export function reorderCuttingPlans(body: {
  run_id: number
  machine_id: number
  ordered_item_ids: number[]
  horizon_days?: number
}): Promise<CuttingPlanningListResponse> {
  return request.post(`${BASE}/reorder`, body)
}

export function publishCuttingPlans(body: {
  run_id: number
  item_ids?: number[] | null
  overwrite_existing?: boolean
}): Promise<{ success: boolean; published_count: number; data: CuttingPlanningListResponse }> {
  return request.post(`${BASE}/publish`, body)
}

export function lockCuttingPlanningItem(body: {
  run_id: number
  item_id: number
  is_locked: boolean
}): Promise<CuttingPlanningListResponse> {
  return request.post(`${BASE}/lock`, body)
}

export function fetchCuttingPlanningGantt(params: {
  productionMonth: string
  runId?: number | null
  startDate?: string | null
  endDate?: string | null
}): Promise<CuttingPlanningGanttResponse> {
  return request.get(`${BASE}/gantt`, { params })
}

export function fetchCuttingPlanningHourlyGantt(params: {
  productionMonth: string
  runId?: number | null
  machineId?: number | null
}): Promise<CuttingPlanningHourlyResponse> {
  return request.get(`${BASE}/hourly-gantt`, { params })
}

export function fetchCuttingPlanningProgress(params: {
  productionMonth: string
}): Promise<CuttingPlanningProgressResponse> {
  return request.get(`${BASE}/progress`, { params })
}

export function fetchCuttingPlanningReport(params: {
  productionMonth: string
}): Promise<CuttingPlanningReportResponse> {
  return request.get(`${BASE}/report`, { params })
}

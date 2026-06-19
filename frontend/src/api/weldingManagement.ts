/**
 * 溶接指示 welding_management（/api/plan/welding-management/*）
 */
import request from '@/shared/api/request'

const LIST = '/api/plan/welding-management/list'

/** クエリ mes_operator_user_id：空文字・null は送らない（FastAPI int パースエラー防止） */
function optionalOperatorUserId(value?: number | null | ''): number | undefined {
  if (value === '' || value == null) return undefined
  return value
}

export interface WeldingManagementListRow {
  id?: number
  production_month?: string | null
  production_day?: string | null
  production_sequence?: number | null
  product_cd?: string | null
  product_name?: string | null
  welding_machine?: string | null
  actual_production_quantity?: number | null
  defect_qty?: number | null
  mes_defect_by_item?: Record<string, number> | null
  production_completed_check?: number | null
  mes_production_started_at?: string | null
  mes_production_ended_at?: string | null
  mes_net_production_sec?: number | null
  mes_paused_accum_sec?: number | null
  mes_shift_sec?: number | null
  mes_break_sec?: number | null
  mes_stop_sec?: number | null
  mes_production_is_paused?: number | null
  mes_operator_user_id?: number | null
  mes_client_instance_id?: string | null
  data_source?: string | null
  external_sync_key?: string | null
  remarks?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface WeldingManagementListResponse {
  success?: boolean
  data?: WeldingManagementListRow[]
  message?: string
}

export function fetchWeldingManagementList(params: {
  production_day?: string | null
  welding_machine?: string | null
  hide_completed?: boolean
  limit?: number
}): Promise<WeldingManagementListResponse> {
  return request.get(LIST, {
    params: {
      production_day: params.production_day,
      welding_machine: params.welding_machine?.trim() || undefined,
      hide_completed: params.hide_completed ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<WeldingManagementListResponse>
}

export interface WeldingMonitorSummaryResponse {
  success?: boolean
  data?: WeldingManagementListRow[]
  /** サーバー取得時刻（ISO 8601） */
  fetched_at?: string
  message?: string
}

/** 溶接モニタ専用：MES データ + メニュー権限（MES_MONITOR_WELDING） */
export function fetchWeldingMonitorSummary(params: {
  production_day: string
  limit?: number
}): Promise<WeldingMonitorSummaryResponse> {
  return request.get('/api/plan/welding-management/monitor-summary', {
    params: {
      production_day: params.production_day,
      limit: params.limit,
    },
  }) as Promise<WeldingMonitorSummaryResponse>
}

export interface CreateWeldingManagementBody {
  production_day: string
  product_cd: string
  product_name: string
  welding_machine?: string
  mes_operator_user_id?: number
  remarks?: string | null
}

export function createWeldingManagement(
  body: CreateWeldingManagementBody,
): Promise<{ success?: boolean; data?: { id?: number }; message?: string }> {
  return request.post('/api/plan/welding-management', body) as Promise<{
    success?: boolean
    data?: { id?: number }
    message?: string
  }>
}

export interface PatchWeldingManagementBody {
  production_day?: string | null
  welding_machine?: string | null
  production_sequence?: number
  actual_production_quantity?: number
  production_completed_check?: boolean
  defect_qty?: number
  remarks?: string | null
  mes_production_started_at?: string
  mes_production_ended_at?: string
  mes_net_production_sec?: number
  mes_paused_accum_sec?: number
  mes_shift_sec?: number
  mes_break_sec?: number
  mes_stop_sec?: number
  mes_production_is_paused?: number
  mes_operator_user_id?: number
  mes_defect_by_item?: Record<string, number | { qty?: number; at?: string }> | string | null
  mes_client_instance_id?: string
  mes_claim_client_lock?: boolean
  mes_release_client_lock?: boolean
  mes_force_release?: boolean
}

export function patchWeldingManagement(
  weldingId: number,
  body: PatchWeldingManagementBody,
): Promise<{ success?: boolean; message?: string }> {
  return request.patch(`/api/plan/welding-management/${weldingId}`, body) as Promise<{
    success?: boolean
    message?: string
  }>
}

export interface WeldingProductivityBucket {
  session_count?: number
  completed_session_count?: number
  sum_actual_qty?: number
  sum_defect_qty?: number
  sum_net_production_sec?: number
  sum_net_production_min?: number
  sum_paused_sec?: number
  sum_paused_min?: number
  defect_rate_percent?: number | null
  efficiency_per_hour?: number | null
}

export interface WeldingProductivityDailyRow extends WeldingProductivityBucket {
  day: string
}

export interface WeldingProductivityOperatorRow extends WeldingProductivityBucket {
  operator_user_id?: number | null
  operator_name?: string
  rank?: number
}

export interface WeldingProductivityProductOperatorRanking {
  product_cd: string
  product_name?: string
  sum_actual_qty?: number
  session_count?: number
  operator_count?: number
  ranked_operator_count?: number
  top_operator_name?: string | null
  top_efficiency_per_hour?: number | null
  operators: WeldingProductivityOperatorRow[]
}

export interface WeldingProductivityProductRow extends WeldingProductivityBucket {
  product_cd?: string
  product_name?: string
}

export interface WeldingProductivityDefectRow {
  defect_cd: string
  qty: number
}

export interface WeldingProductivitySessionRow extends WeldingManagementListRow {
  net_production_sec?: number
  paused_sec?: number
  net_production_min?: number
  paused_min?: number
  efficiency_per_hour?: number | null
  defect_rate_percent?: number | null
  is_completed?: boolean
  operator_display_name?: string
  mes_operator_name?: string | null
  mes_operator_username?: string | null
}

export interface WeldingProductivityAnalysisData {
  start_date: string
  end_date: string
  include_incomplete: boolean
  summary: WeldingProductivityBucket
  daily: WeldingProductivityDailyRow[]
  by_operator: WeldingProductivityOperatorRow[]
  by_product: WeldingProductivityProductRow[]
  by_product_operator_ranking: WeldingProductivityProductOperatorRanking[]
  defect_by_item: WeldingProductivityDefectRow[]
  sessions: WeldingProductivitySessionRow[]
}

export interface WeldingProductivityAnalysisResponse {
  success?: boolean
  data?: WeldingProductivityAnalysisData
  message?: string
}

export function fetchWeldingProductivityAnalysis(params: {
  start_date: string
  end_date: string
  mes_operator_user_id?: number | null | ''
  product_cd?: string | null
  include_incomplete?: boolean
  limit?: number
}): Promise<WeldingProductivityAnalysisResponse> {
  return request.get('/api/plan/welding-management/productivity-analysis', {
    params: {
      start_date: params.start_date,
      end_date: params.end_date,
      mes_operator_user_id: optionalOperatorUserId(params.mes_operator_user_id),
      product_cd: params.product_cd || undefined,
      include_incomplete: params.include_incomplete ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<WeldingProductivityAnalysisResponse>
}

export interface WeldingUtilizationOperatorRow {
  operator_user_id?: number
  operator_name?: string
  session_count?: number
  completed_session_count?: number
  work_day_count?: number
  scheduled_work_day_count?: number
  sum_net_production_sec?: number
  sum_gross_sec?: number
  sum_regular_sec?: number
  sum_overtime_sec?: number
  sum_net_production_min?: number
  sum_gross_min?: number
  regular_min?: number
  overtime_min?: number
  standard_sec_on_worked_days?: number
  standard_sec_calendar?: number
  utilization_percent?: number | null
  calendar_utilization_percent?: number | null
  overtime_ratio_percent?: number | null
}

export interface WeldingUtilizationDailyOperatorRow {
  day: string
  operator_user_id?: number
  operator_name?: string
  is_scheduled_workday?: boolean
  is_weekend?: boolean
  is_extra_workday?: boolean
  session_count?: number
  completed_session_count?: number
  sum_net_production_sec?: number
  sum_gross_sec?: number
  sum_regular_sec?: number
  sum_overtime_sec?: number
  standard_sec?: number
  scheduled_hours?: number
  sum_net_production_min?: number
  sum_gross_min?: number
  regular_min?: number
  overtime_min?: number
  utilization_percent?: number | null
  load_percent?: number | null
}

export interface WeldingUtilizationDailyRow {
  day: string
  is_scheduled_workday?: boolean
  session_count?: number
  operator_count?: number
  sum_net_production_sec?: number
  sum_regular_sec?: number
  sum_overtime_sec?: number
  sum_net_production_min?: number
  overtime_min?: number
  utilization_percent?: number | null
}

export interface WeldingUtilizationSummary {
  operator_count?: number
  session_count?: number
  completed_session_count?: number
  calendar_workdays_in_range?: number
  sum_net_production_sec?: number
  sum_regular_sec?: number
  sum_overtime_sec?: number
  sum_net_production_min?: number
  regular_min?: number
  overtime_min?: number
  utilization_percent?: number | null
  calendar_utilization_percent?: number | null
  unassigned_session_count?: number
  sessions_without_time_count?: number
}

export interface WeldingUtilizationSessionGap {
  id: number
  production_day: string
  operator_user_id?: number | null
  operator_name?: string | null
  product_cd?: string | null
  product_name?: string | null
  production_completed_check?: boolean
  mes_production_started_at?: string | null
  mes_production_ended_at?: string | null
}

export interface WeldingUtilizationAnalysisData {
  start_date: string
  end_date: string
  include_incomplete: boolean
  standard_workday_hours: number
  standard_workday_sec: number
  operator_schedule_applied?: boolean
  default_standard_workday_hours?: number
  extra_workdays: string[]
  extra_holidays: string[]
  company_calendar_applied?: boolean
  company_calendar_extra_workdays?: string[]
  company_calendar_holidays?: string[]
  calendar_workdays_in_range: number
  summary: WeldingUtilizationSummary
  by_operator: WeldingUtilizationOperatorRow[]
  daily_by_operator: WeldingUtilizationDailyOperatorRow[]
  daily: WeldingUtilizationDailyRow[]
  data_gaps: string[]
  sessions_without_time?: WeldingUtilizationSessionGap[]
}

export interface WeldingUtilizationAnalysisResponse {
  success?: boolean
  data?: WeldingUtilizationAnalysisData
  message?: string
}

export function fetchWeldingUtilizationAnalysis(params: {
  start_date: string
  end_date: string
  mes_operator_user_id?: number | null | ''
  include_incomplete?: boolean
  extra_workdays?: string
  extra_holidays?: string
  use_company_calendar?: boolean
  limit?: number
}): Promise<WeldingUtilizationAnalysisResponse> {
  return request.get('/api/plan/welding-management/utilization-analysis', {
    params: {
      start_date: params.start_date,
      end_date: params.end_date,
      mes_operator_user_id: optionalOperatorUserId(params.mes_operator_user_id),
      include_incomplete: params.include_incomplete ? true : undefined,
      extra_workdays: params.extra_workdays || undefined,
      extra_holidays: params.extra_holidays || undefined,
      use_company_calendar: params.use_company_calendar !== false ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<WeldingUtilizationAnalysisResponse>
}

export interface WeldingQualityBucket {
  session_count?: number
  completed_session_count?: number
  sum_actual_qty?: number
  sum_defect_qty?: number
  defect_rate_percent?: number | null
  sessions_with_defect_count?: number
  defect_item_kinds_count?: number
}

export interface WeldingQualityDailyRow extends WeldingQualityBucket {
  day: string
}

export interface WeldingQualityOperatorRow extends WeldingQualityBucket {
  operator_user_id?: number | null
  operator_name?: string
}

export interface WeldingQualityProductRow extends WeldingQualityBucket {
  product_cd?: string
  product_name?: string
  top_defect_cd?: string | null
  top_defect_qty?: number | null
  top_defect_name?: string | null
}

export interface WeldingQualityDefectRow {
  defect_cd: string
  defect_name?: string
  qty: number
  share_percent?: number | null
  rate_per_actual_percent?: number | null
}

export interface WeldingQualityProductDefectRow {
  product_cd: string
  product_name?: string
  defect_cd: string
  defect_name?: string
  qty: number
}

export interface WeldingQualityDefectBreakdownRow {
  defect_cd: string
  defect_name?: string
  qty: number
}

export interface WeldingQualitySessionRow extends WeldingManagementListRow {
  defect_rate_percent?: number | null
  is_completed?: boolean
  has_defect?: boolean
  operator_display_name?: string
  mes_operator_name?: string | null
  mes_operator_username?: string | null
  defect_breakdown?: WeldingQualityDefectBreakdownRow[]
}

export interface WeldingQualityAnalysisData {
  start_date: string
  end_date: string
  include_incomplete: boolean
  summary: WeldingQualityBucket
  daily: WeldingQualityDailyRow[]
  by_operator: WeldingQualityOperatorRow[]
  by_product: WeldingQualityProductRow[]
  defect_by_item: WeldingQualityDefectRow[]
  by_product_defect: WeldingQualityProductDefectRow[]
  sessions: WeldingQualitySessionRow[]
}

export interface WeldingQualityAnalysisResponse {
  success?: boolean
  data?: WeldingQualityAnalysisData
  message?: string
}

export function fetchWeldingQualityAnalysis(params: {
  start_date: string
  end_date: string
  mes_operator_user_id?: number | null | ''
  product_cd?: string | null
  include_incomplete?: boolean
  limit?: number
}): Promise<WeldingQualityAnalysisResponse> {
  return request.get('/api/plan/welding-management/quality-analysis', {
    params: {
      start_date: params.start_date,
      end_date: params.end_date,
      mes_operator_user_id: optionalOperatorUserId(params.mes_operator_user_id),
      product_cd: params.product_cd || undefined,
      include_incomplete: params.include_incomplete ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<WeldingQualityAnalysisResponse>
}


/**
 * 検査指示 inspection_management（/api/plan/inspection-management/*）
 */
import request from '@/shared/api/request'

const LIST = '/api/plan/inspection-management/list'

/** クエリ mes_inspector_user_id：空文字・null は送らない（FastAPI int パースエラー防止） */
function optionalInspectorUserId(value?: number | null | ''): number | undefined {
  if (value === '' || value == null) return undefined
  return value
}

export interface InspectionManagementListRow {
  id?: number
  production_month?: string | null
  production_day?: string | null
  production_sequence?: number | null
  product_cd?: string | null
  product_name?: string | null
  actual_production_quantity?: number | null
  defect_qty?: number | null
  mes_defect_by_item?: Record<string, number> | null
  production_completed_check?: number | null
  mes_production_started_at?: string | null
  mes_production_ended_at?: string | null
  mes_net_production_sec?: number | null
  mes_paused_accum_sec?: number | null
  mes_production_is_paused?: number | null
  mes_inspector_user_id?: number | null
  mes_client_instance_id?: string | null
  /** mes=検査実績収集, excel=管理指標Excel同期, csv=一括取込 */
  data_source?: 'mes' | 'excel' | 'csv' | string | null
  external_sync_key?: string | null
  remarks?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface InspectionManagementListResponse {
  success?: boolean
  data?: InspectionManagementListRow[]
  message?: string
}

export function fetchInspectionManagementList(params: {
  production_day?: string | null
  hide_completed?: boolean
  data_source?: 'mes' | 'excel' | 'csv' | null
  limit?: number
}): Promise<InspectionManagementListResponse> {
  return request.get(LIST, {
    params: {
      production_day: params.production_day,
      hide_completed: params.hide_completed ? true : undefined,
      data_source: params.data_source ?? undefined,
      limit: params.limit,
    },
  }) as Promise<InspectionManagementListResponse>
}

export interface CreateInspectionManagementBody {
  production_day: string
  product_cd: string
  product_name: string
  mes_inspector_user_id?: number
  remarks?: string | null
}

export function createInspectionManagement(
  body: CreateInspectionManagementBody,
): Promise<{ success?: boolean; data?: { id?: number }; message?: string }> {
  return request.post('/api/plan/inspection-management', body) as Promise<{
    success?: boolean
    data?: { id?: number }
    message?: string
  }>
}

export interface PatchInspectionManagementBody {
  production_day?: string | null
  production_sequence?: number
  actual_production_quantity?: number
  production_completed_check?: boolean
  defect_qty?: number
  remarks?: string | null
  mes_production_started_at?: string
  mes_production_ended_at?: string
  mes_net_production_sec?: number
  mes_paused_accum_sec?: number
  mes_production_is_paused?: number
  mes_inspector_user_id?: number
  mes_defect_by_item?: Record<string, number> | string | null
  /** 端末 UUID（localStorage） */
  mes_client_instance_id?: string
  /** 在産行の操作権を取得 */
  mes_claim_client_lock?: boolean
  /** 他端末ロックを無視して終了（強制終了） */
  mes_force_release?: boolean
}

export function patchInspectionManagement(
  inspectionId: number,
  body: PatchInspectionManagementBody,
): Promise<{ success?: boolean; message?: string }> {
  return request.patch(`/api/plan/inspection-management/${inspectionId}`, body) as Promise<{
    success?: boolean
    message?: string
  }>
}

export interface InspectionProductivityBucket {
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

export interface InspectionProductivityDailyRow extends InspectionProductivityBucket {
  day: string
}

export interface InspectionProductivityInspectorRow extends InspectionProductivityBucket {
  inspector_user_id?: number | null
  inspector_name?: string
  rank?: number
}

export interface InspectionProductivityProductInspectorRanking {
  product_cd: string
  product_name?: string
  sum_actual_qty?: number
  session_count?: number
  inspector_count?: number
  ranked_inspector_count?: number
  top_inspector_name?: string | null
  top_efficiency_per_hour?: number | null
  inspectors: InspectionProductivityInspectorRow[]
}

export interface InspectionProductivityProductRow extends InspectionProductivityBucket {
  product_cd?: string
  product_name?: string
}

export interface InspectionProductivityDefectRow {
  defect_cd: string
  qty: number
}

export interface InspectionProductivitySessionRow extends InspectionManagementListRow {
  net_production_sec?: number
  paused_sec?: number
  net_production_min?: number
  paused_min?: number
  efficiency_per_hour?: number | null
  defect_rate_percent?: number | null
  is_completed?: boolean
  inspector_display_name?: string
  mes_inspector_name?: string | null
  mes_inspector_username?: string | null
}

export interface InspectionProductivityAnalysisData {
  start_date: string
  end_date: string
  include_incomplete: boolean
  summary: InspectionProductivityBucket
  daily: InspectionProductivityDailyRow[]
  by_inspector: InspectionProductivityInspectorRow[]
  by_product: InspectionProductivityProductRow[]
  by_product_inspector_ranking: InspectionProductivityProductInspectorRanking[]
  defect_by_item: InspectionProductivityDefectRow[]
  sessions: InspectionProductivitySessionRow[]
}

export interface InspectionProductivityAnalysisResponse {
  success?: boolean
  data?: InspectionProductivityAnalysisData
  message?: string
}

export interface InspectionManagementInspectorOption {
  id: number
  full_name?: string | null
  username?: string | null
}

export interface InspectionManagementInspectorsResponse {
  success?: boolean
  data?: InspectionManagementInspectorOption[]
  message?: string
}

/** inspection_management に登場する検査員（任意で集計期間で絞り込み） */
export function fetchInspectionManagementInspectors(params?: {
  start_date?: string
  end_date?: string
}): Promise<InspectionManagementInspectorsResponse> {
  return request.get('/api/plan/inspection-management/inspectors', {
    params: {
      start_date: params?.start_date,
      end_date: params?.end_date,
    },
  }) as Promise<InspectionManagementInspectorsResponse>
}

export function fetchInspectionProductivityAnalysis(params: {
  start_date: string
  end_date: string
  mes_inspector_user_id?: number | null | ''
  product_cd?: string | null
  include_incomplete?: boolean
  limit?: number
}): Promise<InspectionProductivityAnalysisResponse> {
  return request.get('/api/plan/inspection-management/productivity-analysis', {
    params: {
      start_date: params.start_date,
      end_date: params.end_date,
      mes_inspector_user_id: optionalInspectorUserId(params.mes_inspector_user_id),
      product_cd: params.product_cd || undefined,
      include_incomplete: params.include_incomplete ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<InspectionProductivityAnalysisResponse>
}

export interface InspectionUtilizationInspectorRow {
  inspector_user_id?: number
  inspector_name?: string
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

export interface InspectionUtilizationDailyInspectorRow {
  day: string
  inspector_user_id?: number
  inspector_name?: string
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
  sum_net_production_min?: number
  sum_gross_min?: number
  regular_min?: number
  overtime_min?: number
  utilization_percent?: number | null
  load_percent?: number | null
}

export interface InspectionUtilizationDailyRow {
  day: string
  is_scheduled_workday?: boolean
  session_count?: number
  inspector_count?: number
  sum_net_production_sec?: number
  sum_regular_sec?: number
  sum_overtime_sec?: number
  sum_net_production_min?: number
  utilization_percent?: number | null
}

export interface InspectionUtilizationSummary {
  inspector_count?: number
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

export interface InspectionUtilizationAnalysisData {
  start_date: string
  end_date: string
  include_incomplete: boolean
  standard_workday_hours: number
  standard_workday_sec: number
  extra_workdays: string[]
  extra_holidays: string[]
  company_calendar_applied?: boolean
  company_calendar_extra_workdays?: string[]
  company_calendar_holidays?: string[]
  calendar_workdays_in_range: number
  summary: InspectionUtilizationSummary
  by_inspector: InspectionUtilizationInspectorRow[]
  daily_by_inspector: InspectionUtilizationDailyInspectorRow[]
  daily: InspectionUtilizationDailyRow[]
  data_gaps: string[]
}

export interface InspectionUtilizationAnalysisResponse {
  success?: boolean
  data?: InspectionUtilizationAnalysisData
  message?: string
}

export function fetchInspectionUtilizationAnalysis(params: {
  start_date: string
  end_date: string
  mes_inspector_user_id?: number | null | ''
  include_incomplete?: boolean
  extra_workdays?: string
  extra_holidays?: string
  use_company_calendar?: boolean
  limit?: number
}): Promise<InspectionUtilizationAnalysisResponse> {
  return request.get('/api/plan/inspection-management/utilization-analysis', {
    params: {
      start_date: params.start_date,
      end_date: params.end_date,
      mes_inspector_user_id: optionalInspectorUserId(params.mes_inspector_user_id),
      include_incomplete: params.include_incomplete ? true : undefined,
      extra_workdays: params.extra_workdays || undefined,
      extra_holidays: params.extra_holidays || undefined,
      use_company_calendar: params.use_company_calendar !== false ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<InspectionUtilizationAnalysisResponse>
}

export interface InspectionQualityBucket {
  session_count?: number
  completed_session_count?: number
  sum_actual_qty?: number
  sum_defect_qty?: number
  defect_rate_percent?: number | null
  sessions_with_defect_count?: number
  defect_item_kinds_count?: number
}

export interface InspectionQualityDailyRow extends InspectionQualityBucket {
  day: string
}

export interface InspectionQualityInspectorRow extends InspectionQualityBucket {
  inspector_user_id?: number | null
  inspector_name?: string
}

export interface InspectionQualityProductRow extends InspectionQualityBucket {
  product_cd?: string
  product_name?: string
  top_defect_cd?: string | null
  top_defect_qty?: number | null
  top_defect_name?: string | null
}

export interface InspectionQualityDefectRow {
  defect_cd: string
  defect_name?: string
  qty: number
  share_percent?: number | null
  rate_per_actual_percent?: number | null
}

export interface InspectionQualityProductDefectRow {
  product_cd: string
  product_name?: string
  defect_cd: string
  defect_name?: string
  qty: number
}

export interface InspectionQualityDefectBreakdownRow {
  defect_cd: string
  defect_name?: string
  qty: number
}

export interface InspectionQualitySessionRow extends InspectionManagementListRow {
  defect_rate_percent?: number | null
  is_completed?: boolean
  has_defect?: boolean
  inspector_display_name?: string
  mes_inspector_name?: string | null
  mes_inspector_username?: string | null
  defect_breakdown?: InspectionQualityDefectBreakdownRow[]
}

export interface InspectionQualityAnalysisData {
  start_date: string
  end_date: string
  include_incomplete: boolean
  summary: InspectionQualityBucket
  daily: InspectionQualityDailyRow[]
  by_inspector: InspectionQualityInspectorRow[]
  by_product: InspectionQualityProductRow[]
  defect_by_item: InspectionQualityDefectRow[]
  by_product_defect: InspectionQualityProductDefectRow[]
  sessions: InspectionQualitySessionRow[]
}

export interface InspectionQualityAnalysisResponse {
  success?: boolean
  data?: InspectionQualityAnalysisData
  message?: string
}

export function fetchInspectionQualityAnalysis(params: {
  start_date: string
  end_date: string
  mes_inspector_user_id?: number | null | ''
  product_cd?: string | null
  include_incomplete?: boolean
  limit?: number
}): Promise<InspectionQualityAnalysisResponse> {
  return request.get('/api/plan/inspection-management/quality-analysis', {
    params: {
      start_date: params.start_date,
      end_date: params.end_date,
      mes_inspector_user_id: optionalInspectorUserId(params.mes_inspector_user_id),
      product_cd: params.product_cd || undefined,
      include_incomplete: params.include_incomplete ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<InspectionQualityAnalysisResponse>
}

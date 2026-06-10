/**
 * 検査指示 inspection_management（/api/plan/inspection-management/*）
 */
import request from '@/shared/api/request'

const LIST = '/api/plan/inspection-management/list'

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
  limit?: number
}): Promise<InspectionManagementListResponse> {
  return request.get(LIST, {
    params: {
      production_day: params.production_day,
      hide_completed: params.hide_completed ? true : undefined,
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

export function fetchInspectionProductivityAnalysis(params: {
  start_date: string
  end_date: string
  mes_inspector_user_id?: number | null
  product_cd?: string | null
  include_incomplete?: boolean
  limit?: number
}): Promise<InspectionProductivityAnalysisResponse> {
  return request.get('/api/plan/inspection-management/productivity-analysis', {
    params: {
      start_date: params.start_date,
      end_date: params.end_date,
      mes_inspector_user_id: params.mes_inspector_user_id ?? undefined,
      product_cd: params.product_cd || undefined,
      include_incomplete: params.include_incomplete ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<InspectionProductivityAnalysisResponse>
}

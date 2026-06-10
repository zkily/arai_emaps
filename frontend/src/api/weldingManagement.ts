/**
 * 溶接指示 welding_management（/api/plan/welding-management/*）
 */
import request from '@/shared/api/request'

const LIST = '/api/plan/welding-management/list'

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
  mes_production_is_paused?: number | null
  mes_operator_user_id?: number | null
  mes_client_instance_id?: string | null
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
  mes_production_is_paused?: number
  mes_operator_user_id?: number
  mes_defect_by_item?: Record<string, number> | string | null
  mes_client_instance_id?: string
  mes_claim_client_lock?: boolean
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
  mes_operator_user_id?: number | null
  product_cd?: string | null
  include_incomplete?: boolean
  limit?: number
}): Promise<WeldingProductivityAnalysisResponse> {
  return request.get('/api/plan/welding-management/productivity-analysis', {
    params: {
      start_date: params.start_date,
      end_date: params.end_date,
      mes_operator_user_id: params.mes_operator_user_id ?? undefined,
      product_cd: params.product_cd || undefined,
      include_incomplete: params.include_incomplete ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<WeldingProductivityAnalysisResponse>
}


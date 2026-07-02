/**
 * 面取生産管理指標 chamfering_production_indicator（/api/plan/chamfering-production-indicator/*）
 */
import request from '@/shared/api/request'

export interface ChamferingProductivityBucket {
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

export interface ChamferingProductivityDailyRow extends ChamferingProductivityBucket {
  day: string
}

export interface ChamferingProductivityOperatorRow extends ChamferingProductivityBucket {
  operator_user_id?: number | null
  operator_name?: string
  rank?: number
}

export type ChamferingProductivityLineRow = ChamferingProductivityOperatorRow

export interface ChamferingProductivityProductOperatorRanking {
  product_cd: string
  product_name?: string
  sum_actual_qty?: number
  session_count?: number
  operator_count?: number
  ranked_operator_count?: number
  top_operator_name?: string | null
  top_efficiency_per_hour?: number | null
  operators: ChamferingProductivityOperatorRow[]
}

export type ChamferingProductivityProductLineRanking = ChamferingProductivityProductOperatorRanking

export interface ChamferingProductivityProductRow extends ChamferingProductivityBucket {
  product_cd?: string
  product_name?: string
}

export interface ChamferingProductivityDefectRow {
  defect_cd: string
  qty: number
}

export interface ChamferingProductivitySessionRow {
  id?: number | null
  production_day?: string | null
  product_cd?: string | null
  product_name?: string | null
  actual_production_quantity?: number | null
  defect_qty?: number | null
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

export interface ChamferingProductivityAnalysisData {
  start_date: string
  end_date: string
  include_incomplete: boolean
  summary: ChamferingProductivityBucket
  daily: ChamferingProductivityDailyRow[]
  by_operator: ChamferingProductivityOperatorRow[]
  by_product: ChamferingProductivityProductRow[]
  by_product_operator_ranking: ChamferingProductivityProductOperatorRanking[]
  defect_by_item: ChamferingProductivityDefectRow[]
  sessions: ChamferingProductivitySessionRow[]
}

export interface ChamferingProductivityAnalysisResponse {
  success?: boolean
  data?: ChamferingProductivityAnalysisData
  message?: string
}

export interface ChamferingProductionIndicatorLineOption {
  line_name: string
}

export interface ChamferingProductionIndicatorLinesResponse {
  success?: boolean
  data?: ChamferingProductionIndicatorLineOption[]
  message?: string
}

export function fetchChamferingProductionIndicatorLines(params: {
  start_date: string
  end_date: string
}): Promise<ChamferingProductionIndicatorLinesResponse> {
  return request.get('/api/plan/chamfering-production-indicator/lines', {
    params,
  }) as Promise<ChamferingProductionIndicatorLinesResponse>
}

export function fetchChamferingProductivityAnalysis(params: {
  start_date: string
  end_date: string
  production_line?: string | null
  product_cd?: string | null
  include_incomplete?: boolean
  limit?: number
}): Promise<ChamferingProductivityAnalysisResponse> {
  return request.get('/api/plan/chamfering-production-indicator/productivity-analysis', {
    params: {
      start_date: params.start_date,
      end_date: params.end_date,
      production_line: params.production_line?.trim() || undefined,
      product_cd: params.product_cd || undefined,
      include_incomplete: params.include_incomplete ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<ChamferingProductivityAnalysisResponse>
}

export interface ChamferingProductionIndicatorRow {
  id: number
  fiscal_year?: number | null
  production_month?: string | null
  production_day?: string | null
  source_line?: number | null
  source_file?: string | null
  product_cd?: string | null
  production_line?: string | null
  product_name?: string | null
  chamfer_planned_quantity?: number | null
  chamfer_actual_quantity?: number | null
  chamfer_defect_quantity?: number | null
  sw_planned_quantity?: number | null
  sw_actual_quantity?: number | null
  sw_defect_quantity?: number | null
  shift_hours?: number | null
  break_hours?: number | null
  setup_hours?: number | null
  work_hours?: number | null
  total_production_qty?: number | null
  efficiency_rate?: number | null
  utilization_rate?: number | null
  work_rate?: number | null
  data_source?: 'manual' | 'excel' | 'csv' | string | null
  external_sync_key?: string | null
  remarks?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface ChamferingProductionIndicatorListResponse {
  success?: boolean
  data?: ChamferingProductionIndicatorRow[]
  message?: string
}

export interface ChamferingProductionIndicatorRowResponse {
  success?: boolean
  data?: ChamferingProductionIndicatorRow
  message?: string
}

export interface ChamferingProductionIndicatorManualBody {
  production_day: string
  production_line: string
  product_cd: string
  product_name?: string | null
  chamfer_planned_quantity?: number | null
  chamfer_actual_quantity?: number | null
  chamfer_defect_quantity?: number | null
  sw_planned_quantity?: number | null
  sw_actual_quantity?: number | null
  sw_defect_quantity?: number | null
  shift_hours?: number | null
  break_hours?: number | null
  setup_hours?: number | null
  remarks?: string | null
}

export function fetchChamferingProductionIndicatorList(params: {
  production_day: string
  production_line?: string | null
  limit?: number
}): Promise<ChamferingProductionIndicatorListResponse> {
  return request.get('/api/plan/chamfering-production-indicator/list', {
    params: {
      production_day: params.production_day,
      production_line: params.production_line?.trim() || undefined,
      limit: params.limit,
    },
  }) as Promise<ChamferingProductionIndicatorListResponse>
}

export function createChamferingProductionIndicatorManual(
  body: ChamferingProductionIndicatorManualBody,
): Promise<ChamferingProductionIndicatorRowResponse> {
  return request.post('/api/plan/chamfering-production-indicator/manual', body) as Promise<
    ChamferingProductionIndicatorRowResponse
  >
}

export function patchChamferingProductionIndicator(
  id: number,
  body: Partial<ChamferingProductionIndicatorManualBody>,
): Promise<ChamferingProductionIndicatorRowResponse> {
  return request.patch(`/api/plan/chamfering-production-indicator/${id}`, body) as Promise<
    ChamferingProductionIndicatorRowResponse
  >
}

export function deleteChamferingProductionIndicator(id: number): Promise<{ success?: boolean; message?: string }> {
  return request.delete(`/api/plan/chamfering-production-indicator/${id}`) as Promise<{
    success?: boolean
    message?: string
  }>
}

/**
 * メッキ生産管理指標 plating_production_indicator（/api/plan/plating-production-indicator/*）
 */
import request from '@/shared/api/request'

export interface PlatingProductivityBucket {
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

export interface PlatingProductivityDailyRow extends PlatingProductivityBucket {
  day: string
}

export interface PlatingProductivityOperatorRow extends PlatingProductivityBucket {
  operator_user_id?: number | null
  operator_name?: string
  rank?: number
}

export type PlatingProductivityLineRow = PlatingProductivityOperatorRow

export interface PlatingProductivityProductOperatorRanking {
  product_cd: string
  product_name?: string
  sum_actual_qty?: number
  session_count?: number
  operator_count?: number
  ranked_operator_count?: number
  top_operator_name?: string | null
  top_efficiency_per_hour?: number | null
  operators: PlatingProductivityOperatorRow[]
}

export type PlatingProductivityProductLineRanking = PlatingProductivityProductOperatorRanking

export interface PlatingProductivityProductRow extends PlatingProductivityBucket {
  product_cd?: string
  product_name?: string
}

export interface PlatingProductivityDefectRow {
  defect_cd: string
  qty: number
}

export interface PlatingProductivitySessionRow {
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

export interface PlatingProductivityAnalysisData {
  start_date: string
  end_date: string
  include_incomplete: boolean
  summary: PlatingProductivityBucket
  daily: PlatingProductivityDailyRow[]
  by_operator: PlatingProductivityOperatorRow[]
  by_product: PlatingProductivityProductRow[]
  by_product_operator_ranking: PlatingProductivityProductOperatorRanking[]
  defect_by_item: PlatingProductivityDefectRow[]
  sessions: PlatingProductivitySessionRow[]
}

export interface PlatingProductivityAnalysisResponse {
  success?: boolean
  data?: PlatingProductivityAnalysisData
  message?: string
}

export interface PlatingProductionIndicatorLineOption {
  line_name: string
}

export interface PlatingProductionIndicatorLinesResponse {
  success?: boolean
  data?: PlatingProductionIndicatorLineOption[]
  message?: string
}

export function fetchPlatingProductionIndicatorLines(params: {
  start_date: string
  end_date: string
}): Promise<PlatingProductionIndicatorLinesResponse> {
  return request.get('/api/plan/plating-production-indicator/lines', {
    params,
  }) as Promise<PlatingProductionIndicatorLinesResponse>
}

export function fetchPlatingProductivityAnalysis(params: {
  start_date: string
  end_date: string
  production_line?: string | null
  product_cd?: string | null
  include_incomplete?: boolean
  limit?: number
}): Promise<PlatingProductivityAnalysisResponse> {
  return request.get('/api/plan/plating-production-indicator/productivity-analysis', {
    params: {
      start_date: params.start_date,
      end_date: params.end_date,
      production_line: params.production_line?.trim() || undefined,
      product_cd: params.product_cd || undefined,
      include_incomplete: params.include_incomplete ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<PlatingProductivityAnalysisResponse>
}

export interface PlatingProductionIndicatorRow {
  id: number
  fiscal_year?: number | null
  production_month?: string | null
  production_day?: string | null
  source_line?: number | null
  source_file?: string | null
  planned_quantity?: number | null
  actual_quantity?: number | null
  defect_quantity?: number | null
  defect_plating_scratch?: number | null
  defect_moya_kaburi?: number | null
  defect_nickel?: number | null
  defect_contact?: number | null
  defect_other?: number | null
  shift_hours?: number | null
  maintenance_hours?: number | null
  trouble_hours?: number | null
  choco_stop_hours?: number | null
  planned_stop_hours?: number | null
  available_work_hours?: number | null
  work_hours?: number | null
  total_inspection_qty?: number | null
  efficiency_rate?: number | null
  utilization_rate?: number | null
  work_rate?: number | null
  data_source?: 'manual' | 'excel' | 'csv' | string | null
  external_sync_key?: string | null
  remarks?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface PlatingProductionIndicatorListResponse {
  success?: boolean
  data?: PlatingProductionIndicatorRow[]
  message?: string
}

export interface PlatingProductionIndicatorRowResponse {
  success?: boolean
  data?: PlatingProductionIndicatorRow
  message?: string
}

export interface PlatingProductionIndicatorManualBody {
  production_day: string
  planned_quantity?: number | null
  actual_quantity?: number | null
  defect_quantity?: number | null
  defect_plating_scratch?: number | null
  defect_moya_kaburi?: number | null
  defect_nickel?: number | null
  defect_contact?: number | null
  defect_other?: number | null
  shift_hours?: number | null
  maintenance_hours?: number | null
  trouble_hours?: number | null
  choco_stop_hours?: number | null
  planned_stop_hours?: number | null
  remarks?: string | null
}

export function fetchPlatingProductionIndicatorList(params: {
  production_day: string
  limit?: number
}): Promise<PlatingProductionIndicatorListResponse> {
  return request.get('/api/plan/plating-production-indicator/list', {
    params: {
      production_day: params.production_day,
      limit: params.limit,
    },
  }) as Promise<PlatingProductionIndicatorListResponse>
}

export function createPlatingProductionIndicatorManual(
  body: PlatingProductionIndicatorManualBody,
): Promise<PlatingProductionIndicatorRowResponse> {
  return request.post('/api/plan/plating-production-indicator/manual', body) as Promise<
    PlatingProductionIndicatorRowResponse
  >
}

export function patchPlatingProductionIndicator(
  id: number,
  body: Partial<PlatingProductionIndicatorManualBody>,
): Promise<PlatingProductionIndicatorRowResponse> {
  return request.patch(`/api/plan/plating-production-indicator/${id}`, body) as Promise<
    PlatingProductionIndicatorRowResponse
  >
}

export function deletePlatingProductionIndicator(id: number): Promise<{ success?: boolean; message?: string }> {
  return request.delete(`/api/plan/plating-production-indicator/${id}`) as Promise<{
    success?: boolean
    message?: string
  }>
}

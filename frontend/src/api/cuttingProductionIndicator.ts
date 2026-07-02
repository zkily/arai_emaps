/**
 * 切断生産管理指標 cutting_production_indicator（/api/plan/cutting-production-indicator/*）
 */
import request from '@/shared/api/request'

export interface CuttingProductivityBucket {
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

export interface CuttingProductivityDailyRow extends CuttingProductivityBucket {
  day: string
}

export interface CuttingProductivityOperatorRow extends CuttingProductivityBucket {
  operator_user_id?: number | null
  operator_name?: string
  rank?: number
}

export type CuttingProductivityLineRow = CuttingProductivityOperatorRow

export interface CuttingProductivityProductOperatorRanking {
  product_cd: string
  product_name?: string
  sum_actual_qty?: number
  session_count?: number
  operator_count?: number
  ranked_operator_count?: number
  top_operator_name?: string | null
  top_efficiency_per_hour?: number | null
  operators: CuttingProductivityOperatorRow[]
}

export type CuttingProductivityProductLineRanking = CuttingProductivityProductOperatorRanking

export interface CuttingProductivityProductRow extends CuttingProductivityBucket {
  product_cd?: string
  product_name?: string
}

export interface CuttingProductivityDefectRow {
  defect_cd: string
  qty: number
}

export interface CuttingProductivitySessionRow {
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

export interface CuttingProductivityAnalysisData {
  start_date: string
  end_date: string
  include_incomplete: boolean
  summary: CuttingProductivityBucket
  daily: CuttingProductivityDailyRow[]
  by_operator: CuttingProductivityOperatorRow[]
  by_product: CuttingProductivityProductRow[]
  by_product_operator_ranking: CuttingProductivityProductOperatorRanking[]
  defect_by_item: CuttingProductivityDefectRow[]
  sessions: CuttingProductivitySessionRow[]
}

export interface CuttingProductivityAnalysisResponse {
  success?: boolean
  data?: CuttingProductivityAnalysisData
  message?: string
}

export interface CuttingProductionIndicatorLineOption {
  line_name: string
}

export interface CuttingProductionIndicatorLinesResponse {
  success?: boolean
  data?: CuttingProductionIndicatorLineOption[]
  message?: string
}

export function fetchCuttingProductionIndicatorLines(params: {
  start_date: string
  end_date: string
}): Promise<CuttingProductionIndicatorLinesResponse> {
  return request.get('/api/plan/cutting-production-indicator/lines', {
    params,
  }) as Promise<CuttingProductionIndicatorLinesResponse>
}

export function fetchCuttingProductivityAnalysis(params: {
  start_date: string
  end_date: string
  production_line?: string | null
  product_cd?: string | null
  include_incomplete?: boolean
  limit?: number
}): Promise<CuttingProductivityAnalysisResponse> {
  return request.get('/api/plan/cutting-production-indicator/productivity-analysis', {
    params: {
      start_date: params.start_date,
      end_date: params.end_date,
      production_line: params.production_line?.trim() || undefined,
      product_cd: params.product_cd || undefined,
      include_incomplete: params.include_incomplete ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<CuttingProductivityAnalysisResponse>
}

export interface CuttingProductionIndicatorRow {
  id: number
  fiscal_year?: number | null
  production_month?: string | null
  production_day?: string | null
  source_line?: number | null
  source_file?: string | null
  product_cd?: string | null
  production_line?: string | null
  product_name?: string | null
  planned_quantity?: number | null
  actual_quantity?: number | null
  quantity_variance?: number | null
  shift_hours?: number | null
  break_hours?: number | null
  setup_hours?: number | null
  repair_hours?: number | null
  work_hours?: number | null
  efficiency_rate?: number | null
  utilization_rate?: number | null
  work_rate?: number | null
  data_source?: 'manual' | 'excel' | 'csv' | string | null
  external_sync_key?: string | null
  remarks?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface CuttingProductionIndicatorListResponse {
  success?: boolean
  data?: CuttingProductionIndicatorRow[]
  message?: string
}

export interface CuttingProductionIndicatorRowResponse {
  success?: boolean
  data?: CuttingProductionIndicatorRow
  message?: string
}

export interface CuttingProductionIndicatorManualBody {
  production_day: string
  production_line: string
  product_cd: string
  product_name?: string | null
  planned_quantity?: number | null
  actual_quantity: number
  quantity_variance?: number | null
  shift_hours?: number | null
  break_hours?: number | null
  setup_hours?: number | null
  remarks?: string | null
}

export function fetchCuttingProductionIndicatorList(params: {
  production_day: string
  production_line?: string | null
  limit?: number
}): Promise<CuttingProductionIndicatorListResponse> {
  return request.get('/api/plan/cutting-production-indicator/list', {
    params: {
      production_day: params.production_day,
      production_line: params.production_line?.trim() || undefined,
      limit: params.limit,
    },
  }) as Promise<CuttingProductionIndicatorListResponse>
}

export function createCuttingProductionIndicatorManual(
  body: CuttingProductionIndicatorManualBody,
): Promise<CuttingProductionIndicatorRowResponse> {
  return request.post('/api/plan/cutting-production-indicator/manual', body) as Promise<
    CuttingProductionIndicatorRowResponse
  >
}

export function patchCuttingProductionIndicator(
  id: number,
  body: Partial<CuttingProductionIndicatorManualBody>,
): Promise<CuttingProductionIndicatorRowResponse> {
  return request.patch(`/api/plan/cutting-production-indicator/${id}`, body) as Promise<
    CuttingProductionIndicatorRowResponse
  >
}

export function deleteCuttingProductionIndicator(id: number): Promise<{ success?: boolean; message?: string }> {
  return request.delete(`/api/plan/cutting-production-indicator/${id}`) as Promise<{
    success?: boolean
    message?: string
  }>
}

/**
 * 成形生産管理指標 forming_production_indicator（/api/plan/forming-production-indicator/*）
 */
import request from '@/shared/api/request'

export interface FormingProductivityBucket {
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

export interface FormingProductivityDailyRow extends FormingProductivityBucket {
  day: string
}

export interface FormingProductivityOperatorRow extends FormingProductivityBucket {
  operator_user_id?: number | null
  operator_name?: string
  rank?: number
}

export type FormingProductivityLineRow = FormingProductivityOperatorRow

export interface FormingProductivityProductOperatorRanking {
  product_cd: string
  product_name?: string
  sum_actual_qty?: number
  session_count?: number
  operator_count?: number
  ranked_operator_count?: number
  top_operator_name?: string | null
  top_efficiency_per_hour?: number | null
  operators: FormingProductivityOperatorRow[]
}

export type FormingProductivityProductLineRanking = FormingProductivityProductOperatorRanking

export interface FormingProductivityProductRow extends FormingProductivityBucket {
  product_cd?: string
  product_name?: string
}

export interface FormingProductivityDefectRow {
  defect_cd: string
  qty: number
}

export interface FormingProductivitySessionRow {
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

export interface FormingProductivityAnalysisData {
  start_date: string
  end_date: string
  include_incomplete: boolean
  summary: FormingProductivityBucket
  daily: FormingProductivityDailyRow[]
  by_operator: FormingProductivityOperatorRow[]
  by_product: FormingProductivityProductRow[]
  by_product_operator_ranking: FormingProductivityProductOperatorRanking[]
  defect_by_item: FormingProductivityDefectRow[]
  sessions: FormingProductivitySessionRow[]
}

export interface FormingProductivityAnalysisResponse {
  success?: boolean
  data?: FormingProductivityAnalysisData
  message?: string
}

export interface FormingProductionIndicatorLineOption {
  line_name: string
}

export interface FormingProductionIndicatorLinesResponse {
  success?: boolean
  data?: FormingProductionIndicatorLineOption[]
  message?: string
}

export function fetchFormingProductionIndicatorLines(params: {
  start_date: string
  end_date: string
}): Promise<FormingProductionIndicatorLinesResponse> {
  return request.get('/api/plan/forming-production-indicator/lines', {
    params,
  }) as Promise<FormingProductionIndicatorLinesResponse>
}

export function fetchFormingProductivityAnalysis(params: {
  start_date: string
  end_date: string
  production_line?: string | null
  product_cd?: string | null
  include_incomplete?: boolean
  limit?: number
}): Promise<FormingProductivityAnalysisResponse> {
  return request.get('/api/plan/forming-production-indicator/productivity-analysis', {
    params: {
      start_date: params.start_date,
      end_date: params.end_date,
      production_line: params.production_line?.trim() || undefined,
      product_cd: params.product_cd || undefined,
      include_incomplete: params.include_incomplete ? true : undefined,
      limit: params.limit,
    },
  }) as Promise<FormingProductivityAnalysisResponse>
}

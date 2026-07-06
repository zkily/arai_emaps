/**
 * 管理コード → 日内示帰属 API
 */
import request from '@/utils/request'

const BASE = '/api/database/lot-forecast-attribution'

/** 全品番・長期間の再計算は数分かかることがある */
const RECOMPUTE_TIMEOUT_MS = 5 * 60 * 1000

export interface LotForecastAttributionRow {
  id?: number
  management_code?: string | null
  aps_batch_plan_id?: number | null
  product_cd?: string
  canonical_product_cd?: string
  product_name?: string | null
  demand_product_name?: string | null
  demand_product_cd?: string | null
  destination_cd?: string | null
  destination_name?: string | null
  process_key?: string
  source_date?: string | null
  forecast_attribution_date?: string | null
  attributed_qty?: number
  method?: string
  allocation_rule?: string | null
  attribution_mode?: string
  confidence?: string
  source_entity?: string | null
  source_entity_id?: number | null
  run_id?: string
  cutting_completed?: boolean
  molding_completed?: boolean
  cutting_completed_source?: 'AUTO' | 'MANUAL'
  molding_completed_source?: 'AUTO' | 'MANUAL'
  status_override?: boolean
  status_remark?: string | null
  current_process_key?: string | null
  current_process_label?: string | null
  /** 生産日 + (forming_process_lt − inspection_process_lt) 営業日 */
  predicted_production_completion_date?: string | null
  predicted_production_completion_lt_days?: number | null
}

export type ProcessStatusTriState = 'auto' | 'done' | 'pending'

export interface ProcessStatusOverrideBody {
  management_code: string
  aps_batch_plan_id?: number | null
  cutting_completed?: boolean | null
  molding_completed?: boolean | null
  remark?: string | null
}

export interface ForecastAttributionDestination {
  destination_cd: string
  demand_product_cd?: string | null
  attributed_qty?: number
}

export interface ForecastAttributionSummary {
  primary_forecast_date?: string | null
  by_date?: Record<string, number>
  destinations?: ForecastAttributionDestination[]
  attribution_mode?: string | null
}

export interface RecomputeAttributionBody {
  startDate: string
  productCds?: string[]
  modes?: ('PLAN' | 'ACTUAL')[]
}

export interface LotForecastAttributionListResponse {
  code?: number
  data?: LotForecastAttributionRow[]
  total?: number
}

export interface LotForecastAttributionRecomputeResponse {
  code?: number
  data?: { run_id?: string; inserted?: number }
  message?: string
}

export function recomputeLotForecastAttribution(body: RecomputeAttributionBody) {
  return request.post(`${BASE}/recompute`, body, {
    timeout: RECOMPUTE_TIMEOUT_MS,
  }) as unknown as Promise<LotForecastAttributionRecomputeResponse>
}

export function getLotForecastAttribution(params: {
  management_code?: string
  product_cd?: string
  destination_cd?: string
  start_date?: string
  end_date?: string
  process_key?: string
  attribution_mode?: string
  prefer_actual?: boolean
}) {
  return request.get(`${BASE}`, { params }) as unknown as Promise<LotForecastAttributionListResponse>
}

export function batchForecastAttributionSummary(management_codes: string[], process_key = 'molding') {
  return request.post<{ code?: number; data?: Record<string, ForecastAttributionSummary> }>(
    `${BASE}/batch-summary`,
    { management_codes, process_key },
  )
}

export function lookupAttributionByManagementCode(
  management_code: string,
  process_key = 'molding',
) {
  return request.get<LotForecastAttributionListResponse>(`${BASE}/lookup`, {
    params: { management_code, process_key },
  }) as unknown as Promise<LotForecastAttributionListResponse>
}

export function batchLookupLotForecastAttribution(
  management_codes: string[],
  process_key = 'molding',
  prefer_actual = false,
  aps_batch_plan_ids?: number[],
  source_date?: string,
) {
  return request.post<LotForecastAttributionListResponse>(`${BASE}/batch-lookup`, {
    management_codes,
    process_key,
    prefer_actual,
    ...(aps_batch_plan_ids?.length ? { aps_batch_plan_ids } : {}),
    ...(source_date ? { source_date } : {}),
  }) as unknown as Promise<LotForecastAttributionListResponse>
}

export function reconcileLotForecastAttribution(params: {
  start_date: string
  end_date: string
  run_id?: string
  canonical_product_cd?: string
}) {
  return request.get<{ code?: number; data?: unknown }>(`${BASE}/reconcile`, { params })
}

export function saveProcessStatusOverride(body: ProcessStatusOverrideBody) {
  return request.put<{ code?: number; data?: ProcessStatusOverrideBody; message?: string }>(
    `${BASE}/process-status-override`,
    body,
  )
}

export function clearProcessStatusOverride(management_code: string) {
  return request.delete<{ code?: number; message?: string }>(`${BASE}/process-status-override`, {
    params: { management_code },
  })
}

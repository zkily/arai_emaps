/**
 * 切断指示 cutting_management（/api/plan/cutting-management/*）
 */
import request from '@/shared/api/request'

const LIST = '/api/plan/cutting-management/list'

/** GET /plan/cutting-management/list の行（レスポンス data の要素） */
export interface CuttingManagementListRow {
  id?: number
  production_month?: string | null
  production_day?: string | null
  production_line?: string | null
  cutting_machine?: string | null
  production_sequence?: number | null
  priority_order?: number | null
  product_cd?: string | null
  product_name?: string | null
  planned_quantity?: number | null
  start_date?: string | null
  end_date?: string | null
  production_lot_size?: number | null
  lot_number?: string | null
  is_cutting_instructed?: number | null
  has_chamfering_process?: number | null
  is_chamfering_instructed?: number | null
  has_sw_process?: number | null
  is_sw_instructed?: number | null
  management_code?: string | null
  actual_production_quantity?: number | null
  defect_qty?: number | null
  take_count?: number | null
  cutting_length?: number | null
  chamfering_length?: number | null
  developed_length?: number | null
  scrap_length?: number | null
  material_name?: string | null
  material_manufacturer?: string | null
  standard_specification?: string | null
  production_completed_check?: number | null
  material_usage_reflected?: string | null
  use_material_stock_sub?: number | null
  usage_count?: number | null
  /** MES 切断実績収集 */
  mes_production_started_at?: string | null
  mes_production_ended_at?: string | null
  mes_net_production_sec?: number | null
  mes_paused_accum_sec?: number | null
  mes_setup_time_min?: number | null
  mes_operator_user_id?: number | null
  mes_scanned_code?: string | null
  cd?: string | null
  production_time?: number | string | null
  remarks?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface CuttingManagementListResponse {
  success?: boolean
  data?: CuttingManagementListRow[]
  message?: string
}

export function fetchCuttingManagementList(params: {
  production_day?: string | null
  production_month?: string | null
  cutting_machine?: string | null
  production_line?: string | null
  limit?: number
}): Promise<CuttingManagementListResponse> {
  return request.get(LIST, { params }) as Promise<CuttingManagementListResponse>
}

export interface PatchCuttingManagementBody {
  actual_production_quantity?: number
  production_completed_check?: boolean
  defect_qty?: number
  remarks?: string | null
  mes_production_started_at?: string
  mes_production_ended_at?: string
  mes_net_production_sec?: number
  mes_paused_accum_sec?: number
  mes_setup_time_min?: number
  mes_operator_user_id?: number
  mes_scanned_code?: string | null
}

export interface SplitCuttingToNextDayBody {
  today_quantity: number
  next_day?: string | null
}

export function patchCuttingManagement(
  cuttingId: number,
  body: PatchCuttingManagementBody,
): Promise<{ success?: boolean; message?: string }> {
  return request.patch(`/api/plan/cutting-management/${cuttingId}`, body) as Promise<{
    success?: boolean
    message?: string
  }>
}

export function splitCuttingManagementToNextDay(
  cuttingId: number,
  body: SplitCuttingToNextDayBody,
): Promise<{ success?: boolean; message?: string }> {
  return request.post(`/api/plan/cutting-management/${cuttingId}/split-to-next-day`, body) as Promise<{
    success?: boolean
    message?: string
  }>
}

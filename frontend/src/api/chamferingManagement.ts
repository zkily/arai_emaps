/**
 * 面取指示 chamfering_management（/api/plan/chamfering-management/*）
 */
import request from '@/shared/api/request'
import { getMachineList } from '@/api/master/machineMaster'
import type { MachineItem } from '@/types/master'

const LIST = '/api/plan/chamfering-management/list'

/** GET /plan/chamfering-management/list の行（レスポンス data の要素） */
export interface ChamferingManagementListRow {
  id?: number
  production_month?: string | null
  production_day?: string | null
  production_line?: string | null
  chamfering_machine?: string | null
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
  /** MES 面取実績収集 */
  mes_production_started_at?: string | null
  mes_production_ended_at?: string | null
  mes_net_production_sec?: number | null
  mes_paused_accum_sec?: number | null
  /** 0=稼働中, 1=一時停止（多端末同期） */
  mes_production_is_paused?: number | null
  mes_setup_time_min?: number | null
  mes_operator_user_id?: number | null
  mes_scanned_code?: string | null
  cd?: string | null
  production_time?: number | string | null
  remarks?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface ChamferingManagementListResponse {
  success?: boolean
  data?: ChamferingManagementListRow[]
  message?: string
}

export function fetchChamferingManagementList(params: {
  production_day?: string | null
  production_month?: string | null
  chamfering_machine?: string | null
  production_line?: string | null
  limit?: number
}): Promise<ChamferingManagementListResponse> {
  return request.get(LIST, { params }) as Promise<ChamferingManagementListResponse>
}

export interface PatchChamferingManagementBody {
  production_day?: string | null
  chamfering_machine?: string | null
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
  mes_setup_time_min?: number
  mes_operator_user_id?: number
  mes_scanned_code?: string | null
}

export interface SplitChamferingToNextDayBody {
  today_quantity: number
  next_day?: string | null
}

export function patchChamferingManagement(
  chamferingId: number,
  body: PatchChamferingManagementBody,
): Promise<{ success?: boolean; message?: string }> {
  return request.patch(`/api/plan/chamfering-management/${chamferingId}`, body) as Promise<{
    success?: boolean
    message?: string
  }>
}

export interface ReorderChamferingManagementBody {
  chamfering_machine: string
  production_day: string
  ordered_ids: number[]
}

export function reorderChamferingManagement(
  body: ReorderChamferingManagementBody,
): Promise<{ success?: boolean; message?: string }> {
  return request.post('/api/plan/chamfering-management/reorder', body) as Promise<{
    success?: boolean
    message?: string
  }>
}

export function splitChamferingManagementToNextDay(
  chamferingId: number,
  body: SplitChamferingToNextDayBody,
): Promise<{ success?: boolean; message?: string }> {
  return request.post(`/api/plan/chamfering-management/${chamferingId}/split-to-next-day`, body) as Promise<{
    success?: boolean
    message?: string
  }>
}

export interface ChamferingMesMachine {
  id: number
  machine_cd: string
  machine_name: string
}

/** 面取機一覧（設備マスタ・名称に「面取」を含む） */
export async function fetchChamferingMesMachines(): Promise<ChamferingMesMachine[]> {
  const result = await getMachineList({ keyword: '面取', pageSize: 500 })
  const list: MachineItem[] = result.data?.list ?? result.list ?? []
  return list
    .filter((r) => r.machine_name && String(r.machine_name).includes('面取'))
    .map((r) => ({
      id: Number(r.id),
      machine_cd: String(r.machine_cd ?? ''),
      machine_name: String(r.machine_name ?? ''),
    }))
    .filter((m) => Number.isFinite(m.id) && m.id > 0)
}

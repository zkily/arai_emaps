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

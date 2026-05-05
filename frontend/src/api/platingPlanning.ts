import request from '@/shared/api/request'

const BASE = '/api/aps/plating/drafts'

export interface PlatingDraftItemBody {
  sort_order: number
  work_date?: string | null
  product_cd: string
  product_name: string
  plating_machine: string
  kake: number
  qty: number
  slots: number
  source_type: 'left_inventory' | 'right_gen'
  source_row_key?: string | null
}

/** 第④看板 1 枠（POST/PUT 写入；plan_date / draft_version_no 由服务端填） */
export interface PlatingBoardCardBody {
  work_date?: string | null
  lap_no: number
  turn_seq: number
  product_cd: string
  product_name: string
  plating_machine: string
  kake: number
  qty: number
  slots: number
  board_mark: string
  stable_key?: string | null
}

export interface PlatingDraftBody {
  plan_date: string
  daily_minutes: number
  jigs_per_lap: number
  minutes_per_lap: number
  total_slots: number
  used_slots: number
  remain_slots: number
  items: PlatingDraftItemBody[]
  board_cards?: PlatingBoardCardBody[] | null
}

export interface PlatingDraftItemOut extends PlatingDraftItemBody {
  id: number
  draft_id: number
}

export interface PlatingBoardCardOut extends PlatingBoardCardBody {
  id: number
  draft_id: number
  plan_date: string
  draft_version_no: number
}

export interface PlatingDraftOut extends Omit<PlatingDraftBody, 'items' | 'board_cards'> {
  id: number
  version_no: number
  status: string
  created_by?: string | null
  updated_by?: string | null
  created_at?: string
  updated_at?: string
  items: PlatingDraftItemOut[]
  board_cards: PlatingBoardCardOut[]
}

export function createPlatingDraft(body: PlatingDraftBody): Promise<PlatingDraftOut> {
  return request.post(BASE, body)
}

export function updatePlatingDraft(id: number, body: PlatingDraftBody): Promise<PlatingDraftOut> {
  return request.put(`${BASE}/${id}`, body)
}

export function fetchLatestPlatingDraftByDate(
  planDate: string,
  opts?: { workDate?: string | null },
): Promise<PlatingDraftOut | null> {
  const params: Record<string, string> = { planDate }
  if (opts?.workDate) params.workDate = opts.workDate
  return request.get(`${BASE}/latest`, { params })
}

/** workDate を渡すと aps_plating_plan_draft_items をその作業日のみ SQL 条件で取得 */
export function fetchPlatingDraftById(id: number, workDate?: string | null): Promise<PlatingDraftOut> {
  return request.get(`${BASE}/${id}`, { params: workDate ? { workDate } : {} })
}

export function deletePlatingDraft(id: number): Promise<{ success: boolean }> {
  return request.delete(`${BASE}/${id}`)
}

export interface PlatingJigAvailabilityItem {
  plating_machine: string
  available_qty: number
}

export interface PlatingJigAvailabilityOut extends PlatingJigAvailabilityItem {
  id: number
  work_date: string
  updated_by?: string | null
}

export function fetchPlatingJigAvailability(workDate: string): Promise<PlatingJigAvailabilityOut[]> {
  return request.get('/api/aps/plating/jig-availability', { params: { workDate } })
}

export function savePlatingJigAvailability(body: {
  work_date: string
  items: PlatingJigAvailabilityItem[]
}): Promise<{ success: boolean }> {
  return request.put('/api/aps/plating/jig-availability', body)
}

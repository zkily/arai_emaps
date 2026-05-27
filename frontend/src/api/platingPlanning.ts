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
  /** 当該周目的日历日（跨日计划） */
  lap_work_date?: string | null
  lap_start_time?: string | null
  lap_end_time?: string | null
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

/** 追加レイアウト 1 ブロック（POST/PUT 写入；カード未配置でも骨格を保存） */
export interface PlatingDraftLayoutBody {
  block_seq: number
  plan_date: string
  start_time: string
  minutes_per_lap: number
  jigs_per_lap: number
  lap_count: number
  base_lap_no: number
}

export interface PlatingDraftBody {
  plan_date: string
  daily_minutes: number
  jigs_per_lap: number
  /** ボード段数（周目数） */
  max_laps: number
  minutes_per_lap: number
  /** ボード第1段開始時刻 HH:mm */
  board_start_time?: string | null
  total_slots: number
  used_slots: number
  remain_slots: number
  items: PlatingDraftItemBody[]
  board_cards?: PlatingBoardCardBody[] | null
  /** 追加レイアウトブロック；None=不更新／配列=全置換 */
  layout_blocks?: PlatingDraftLayoutBody[] | null
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

export interface PlatingDraftLayoutOut extends PlatingDraftLayoutBody {
  id: number
  draft_id: number
}

export interface PlatingDraftOut
  extends Omit<PlatingDraftBody, 'items' | 'board_cards' | 'layout_blocks'> {
  id: number
  version_no: number
  status: string
  created_by?: string | null
  updated_by?: string | null
  created_at?: string
  updated_at?: string
  items: PlatingDraftItemOut[]
  board_cards: PlatingBoardCardOut[]
  layout_blocks: PlatingDraftLayoutOut[]
}

export function createPlatingDraft(body: PlatingDraftBody): Promise<PlatingDraftOut> {
  return request.post(BASE, body)
}

export function updatePlatingDraft(id: number, body: PlatingDraftBody): Promise<PlatingDraftOut> {
  return request.put(`${BASE}/${id}`, body)
}

export interface PlatingDraftFetchOpts {
  /** draft_items の work_date フィルタ（明細のみ） */
  workDate?: string | null
  /** board_cards の表示期間（SQL: coalesce(lap_work_date, work_date, plan_date)） */
  boardFrom?: string | null
  boardTo?: string | null
}

function platingDraftFetchParams(opts?: PlatingDraftFetchOpts | string | null): Record<string, string> {
  const o: PlatingDraftFetchOpts =
    typeof opts === 'string' ? { workDate: opts } : opts ?? {}
  const params: Record<string, string> = {}
  if (o.workDate) params.workDate = o.workDate
  if (o.boardFrom) params.boardFrom = o.boardFrom
  if (o.boardTo) params.boardTo = o.boardTo
  return params
}

export function fetchLatestPlatingDraftByDate(
  planDate: string,
  opts?: PlatingDraftFetchOpts,
): Promise<PlatingDraftOut | null> {
  const params: Record<string, string> = { planDate, ...platingDraftFetchParams(opts) }
  return request.get(`${BASE}/latest`, { params })
}

/** workDate＝明細のみ。boardFrom/boardTo＝aps_plating_plan_board_cards を SQL で期間絞り込み */
export function fetchPlatingDraftById(
  id: number,
  opts?: PlatingDraftFetchOpts | string | null,
): Promise<PlatingDraftOut> {
  return request.get(`${BASE}/${id}`, { params: platingDraftFetchParams(opts) })
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

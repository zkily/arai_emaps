/** 部品購買・受入ログ（part_logs） */
export interface PartLogItem {
  id?: number
  item: string
  part_cd: string
  part_name?: string
  process_cd: string
  log_date: string
  log_time: string
  hd_no?: string
  pieces_per_bundle?: number
  quantity?: number
  bundle_quantity?: number
  manufacture_no?: string
  manufacture_date?: string
  length?: number
  outer_diameter1?: number
  outer_diameter2?: number
  magnetic?: string
  appearance?: string
  supplier?: string
  part_quality?: string
  remarks?: string
  note?: string
  created_at?: string
  updated_at?: string
}

export type PartLog = PartLogItem

export interface PartLogSearchParams {
  keyword?: string
  start_date?: string
  end_date?: string
  supplier?: string | string[]
  page?: number
  page_size?: number
  sort_field?: string
  sort_order?: string
}

/**
 * 材料管理相关类型（与后端 material 模块一致）
 */

/** 検品基準マスタ */
export interface MaterialInspectionMaster {
  id: number
  inspection_cd: string
  inspection_standard: string
  created_at?: string
  updated_at?: string
}

export interface MaterialInspectionSearchParams {
  keyword?: string
  page?: number
  page_size?: number
}

/** 受入ログ（material_logs） */
export interface MaterialLogItem {
  id?: number
  item: string
  material_cd: string
  material_name?: string
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
  material_quality?: string
  remarks?: string
  note?: string
  created_at?: string
  updated_at?: string
}

/** 受入ログ（MaterialLog は MaterialLogItem の別名） */
export type MaterialLog = MaterialLogItem

export interface MaterialLogSearchParams {
  keyword?: string
  start_date?: string
  end_date?: string
  supplier?: string | string[]
  page?: number
  page_size?: number
  sort_field?: string
  sort_order?: string
}

/** 在庫材料（stock_materials） */
export interface StockMaterialItem {
  id?: number
  material_name: string
  manufacture_no: string
  quantity: number
  log_date: string
  supplier?: string
  material_quality?: string
  is_used?: boolean
  note?: string
  created_at?: string
  updated_at?: string
}

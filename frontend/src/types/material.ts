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
  /** 切断ログに同一製造番号がある（includeCuttingUsage 時のみ） */
  used_in_cutting?: boolean
  /** 上記と別に、切断ログ突合の有無（includeCuttingUsage 時のみ） */
  used_in_cutting_from_log?: boolean
  /** 事後手動で「切断使用済」と確定したか */
  cutting_used_manual?: boolean
  cutting_used_manual_at?: string
  cutting_used_manual_by?: string
  cutting_used_manual_note?: string
  /** PUT のみ。手動使用済と同時に切断ログへ management_code を書くとき */
  manual_cutting_management_code?: string
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

/** 製品ー材料照会（kanban_issuance ベース） */
export interface ProductMaterialAssociationItem {
  id: number
  process_type?: string | null
  source_id?: number | null
  kanban_no?: string | null
  issue_date?: string | null
  status?: string | null
  created_at?: string | null
  product_cd?: string | null
  product_name?: string | null
  production_line?: string | null
  cutting_machine?: string | null
  material_name?: string | null
  standard_specification?: string | null
  management_code?: string | null
  start_date?: string | null
  end_date?: string | null
  planned_quantity?: number | null
  production_lot_size?: number | null
  actual_production_quantity?: number | null
  take_count?: number | null
  cutting_length?: number | null
  chamfering_length?: number | null
  developed_length?: number | null
  has_chamfering_process?: boolean
  lot_number?: string | null
  production_day?: string | null
  /** material_cutting_logs.manufacture_no（管理コード突合・最新1件） */
  cutting_log_manufacture_no?: string | null
  /** material_cutting_logs.log_date / log_time（同上） */
  cutting_log_date?: string | null
  cutting_log_time?: string | null
  /** material_logs.manufacture_no 経由（切断ログ manufacture_no → 受入ログ・最新1件） */
  material_log_manufacture_date?: string | null
  material_log_supplier?: string | null
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

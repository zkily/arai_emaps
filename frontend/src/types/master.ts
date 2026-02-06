/**
 * マスタ関連型定義
 */
export interface Product {
  id?: number
  product_cd: string
  product_name: string
  product_type?: string
  location_cd?: string
  start_use_date?: string | Date | null
  category?: string
  department_id?: number | null
  delivery_destination_cd?: string
  process_count?: number
  lead_time?: number
  lot_size?: number
  is_multistage?: boolean
  priority?: number
  status?: string
  part_number?: string
  vehicle_model?: string
  box_type?: string
  unit_per_box?: number
  dimensions?: string
  weight?: number
  material_cd?: string
  cut_length?: number
  chamfer_length?: number
  developed_length?: number
  take_count?: number
  scrap_length?: number
  bom_id?: number
  route_cd?: string
  note?: string
  created_at?: string
  updated_at?: string
  safety_days?: number
  unit_price?: number
  product_alias?: string
}

export interface OptionItem {
  cd: string
  name: string
}

/** 材料マスタ */
export interface Material {
  id?: number
  material_cd: string
  material_name: string
  material_type?: string
  standard_spec?: string
  unit?: string
  diameter?: number
  thickness?: number
  length?: number
  supply_classification?: string
  pieces_per_bundle?: number
  usegae?: string
  supplier_cd?: string
  supplier_name?: string
  unit_price?: number
  long_weight?: number
  single_price?: number
  safety_stock?: number
  lead_time?: number
  storage_location?: string
  status?: number
  tolerance_range?: string
  tolerance_1?: number
  tolerance_2?: number
  range_value?: string
  min_value?: number
  max_value?: number
  actual_value_1?: number
  actual_value_2?: number
  actual_value_3?: number
  representative_model?: string
  note?: string
  created_at?: string
  updated_at?: string
}

/** 仕入先マスタ */
export interface Supplier {
  id?: number
  supplier_cd: string
  supplier_name: string
  supplier_kana?: string
  contact_person?: string
  phone?: string
  fax?: string
  email?: string
  postal_code?: string
  address1?: string
  address2?: string
  payment_terms?: string
  currency?: string
  remarks?: string
  created_at?: string
  updated_at?: string
}

/** 工程ルートマスタ */
export interface RouteItem {
  id?: number
  route_cd: string
  route_name: string
  description?: string
  is_active?: boolean
  is_default?: boolean
  created_at?: string
  updated_at?: string
}

/** 工程ルート1件取得用（ステップ編集ヘッダー） */
export interface RouteInfo {
  route_cd: string
  route_name: string
  description?: string
  is_active?: boolean
  is_default?: boolean
}

/** 工程ルートステップ（製品別） */
export interface RouteStepItem {
  id?: number
  product_cd: string
  route_cd: string
  step_no: number
  process_cd: string
  process_name?: string
  machine_id?: string
  standard_cycle_time?: number
  setup_time?: number
  remarks?: string
  created_at?: string
  updated_at?: string
}

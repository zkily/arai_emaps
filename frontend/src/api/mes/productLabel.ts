/**
 * MES 製品ラベル（現品票）発行 API
 */
import request from '@/shared/api/request'

const BASE = '/api/mes/product-label'

export interface ProductLabelTopRow {
  machine_1: string
  machine_2: string
  machine_3: string
  machine_4_fixed: string
}

export interface ProductLabelPreview {
  product_cd: string
  master_product_name: string
  label_product_name: string
  process_unit_qty: number | null
  paper_color: string
  product_name_color: string
  top_row: ProductLabelTopRow
  process_slots: (string | null)[]
  print_columns: number
  config_id?: number | null
}

export function fetchProductLabelPreview(productCd: string) {
  return request.get<{ success?: boolean; data?: ProductLabelPreview }>(`${BASE}/preview`, {
    params: { product_cd: productCd },
  })
}

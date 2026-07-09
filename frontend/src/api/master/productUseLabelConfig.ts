/**
 * 製品用ラベル設定マスタ API
 */
import request from '@/shared/api/request'

const BASE = '/api/master/product-use-label-config'

export interface ProductUseLabelConfig {
  id?: number
  product_cd: string
  master_product_name?: string
  use_label_product_name?: string | null
  unit_qty?: number | null
  part_no?: string | null
  destination_name?: string | null
  paper_color?: string | null
  product_name_color?: string | null
  back_no_1?: string | null
  back_no_2?: string | null
  back_no_3?: string | null
  barcode_no?: string | null
  is_inoac_layout?: boolean
  product_status?: string | null
  is_discontinued?: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface ProductUseLabelConfigQuery {
  keyword?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface AvailableProductForUseLabel {
  product_cd: string
  product_name: string
  configured: boolean
}

export const PAPER_COLOR_OPTIONS = ['白', '黄', 'ピンク', '緑', '青', 'オレンジ'] as const

export const PRODUCT_NAME_COLOR_OPTIONS = [
  { label: '黒', value: '#000000' },
  { label: '濃紺', value: '#000080' },
  { label: '赤', value: '#CC0000' },
  { label: '深黄', value: '#996600' },
  { label: '深緑', value: '#006400' },
] as const

export function productNameColorLabel(hex?: string | null): string {
  const v = (hex || '#000000').toLowerCase()
  const found = PRODUCT_NAME_COLOR_OPTIONS.find((o) => o.value.toLowerCase() === v)
  return found?.label ?? '黒'
}

export function fetchProductUseLabelConfigList(params?: ProductUseLabelConfigQuery) {
  return request.get<{ list: ProductUseLabelConfig[]; total: number }>(BASE, { params })
}

export function fetchProductUseLabelConfigByProductCd(productCd: string) {
  return request.get<ProductUseLabelConfig>(`${BASE}/by-product/${encodeURIComponent(productCd)}`)
}

export function fetchAvailableProductsForUseLabel() {
  return request.get<{ success?: boolean; data?: AvailableProductForUseLabel[] }>(
    `${BASE}/available-products`
  )
}

export function fetchProductUseLabelPrefill(productCd: string) {
  return request.get<{ success?: boolean; data?: Partial<ProductUseLabelConfig> }>(
    `${BASE}/prefill/${encodeURIComponent(productCd)}`
  )
}

export function syncProductUseLabelFromMaster() {
  return request.post<{
    success?: boolean
    data?: { added: number; updated: number; total_products: number }
  }>(`${BASE}/sync-from-master`)
}

export function importProductUseLabelFromMaster(productCd: string) {
  return request.post<ProductUseLabelConfig>(
    `${BASE}/by-product/${encodeURIComponent(productCd)}/import-from-master`
  )
}

export function createProductUseLabelConfig(data: Partial<ProductUseLabelConfig>) {
  return request.post<ProductUseLabelConfig>(BASE, data)
}

export function updateProductUseLabelConfig(id: number, data: Partial<ProductUseLabelConfig>) {
  return request.put<ProductUseLabelConfig>(`${BASE}/${id}`, data)
}

export function deleteProductUseLabelConfig(id: number) {
  return request.delete<{ success?: boolean }>(`${BASE}/${id}`)
}

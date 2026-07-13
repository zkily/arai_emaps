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
  supply_type?: string | null
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
  product_cd?: string
  destination_name?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface ProductUseLabelFilterProduct {
  product_cd: string
  product_name: string
}

export interface ProductUseLabelFilterOptions {
  products: ProductUseLabelFilterProduct[]
  destinations: string[]
}

export interface AvailableProductForUseLabel {
  product_cd: string
  product_name: string
  configured: boolean
}

export const SUPPLY_TYPE_OPTIONS = ['社内', '外注'] as const

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

export function fetchProductUseLabelFilterOptions() {
  return request.get<{ success?: boolean; data?: ProductUseLabelFilterOptions }>(
    `${BASE}/filter-options`
  )
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

export interface OutsourceOrderEmailItem {
  product_cd: string
  order_qty: number
  use_label_product_name?: string | null
  master_product_name?: string | null
  unit_qty?: number | null
  paper_color?: string | null
}

export interface OutsourceOrderEmailAttachment {
  filename: string
  mime_type: string
  content_base64: string
}

export interface OutsourceOrderEmailPreview {
  success: boolean
  item_count: number
  items: ProductUseLabelConfig[]
  email_enabled: boolean
  smtp_configured: boolean
  template_subject?: string | null
  can_send: boolean
}

export function fetchOutsourceUseLabelOrders() {
  return request.get<{ list: ProductUseLabelConfig[]; total: number }>(`${BASE}/outsource-orders`)
}

export function fetchOutsourceUseLabelOrderEmailPreview() {
  return request.get<OutsourceOrderEmailPreview>(`${BASE}/outsource-order/email-preview`)
}

export function sendOutsourceUseLabelOrderEmail(data: {
  user_ids: number[]
  items: OutsourceOrderEmailItem[]
  attachments: OutsourceOrderEmailAttachment[]
}) {
  return request.post<{
    success: boolean
    message: string
    item_count: number
    total_order_qty: number
    attachment_count: number
    email_sent_count: number
    email_failed?: { email: string; error: string }[]
  }>(`${BASE}/outsource-order/send-email`, data)
}

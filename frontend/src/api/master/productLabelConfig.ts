/**
 * 成型用ラベル設定マスタ API
 */
import request from '@/shared/api/request'

const BASE = '/api/master/product-label-config'

export interface ProductLabelConfig {
  id?: number
  product_cd: string
  master_product_name?: string
  label_product_name?: string | null
  process_unit_qty?: number | null
  process_slots?: (string | null)[]
  process_slot_1?: string | null
  process_slot_2?: string | null
  process_slot_3?: string | null
  process_slot_4?: string | null
  process_slot_5?: string | null
  process_slot_6?: string | null
  process_slot_7?: string | null
  process_slot_8?: string | null
  paper_color?: string | null
  product_name_color?: string | null
  upper_slots_locked?: boolean
  supply_type?: string | null
  remark?: string | null
  route_description?: string | null
  product_status?: string | null
  is_discontinued?: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface ProductLabelConfigQuery {
  keyword?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface AvailableProductForLabel {
  product_cd: string
  product_name: string
  configured: boolean
}

export const PAPER_COLOR_OPTIONS = ['白', '黄', 'ピンク', '緑', '青', 'オレンジ'] as const

export const SUPPLY_TYPE_OPTIONS = ['社内', '外注'] as const

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

export function fetchProductLabelConfigList(params?: ProductLabelConfigQuery) {
  return request.get<{ list: ProductLabelConfig[]; total: number }>(BASE, { params })
}

export function fetchProductLabelConfigByProductCd(productCd: string) {
  return request.get<ProductLabelConfig>(`${BASE}/by-product/${encodeURIComponent(productCd)}`)
}

export function fetchAvailableProductsForLabel() {
  return request.get<{ success?: boolean; data?: AvailableProductForLabel[] }>(
    `${BASE}/available-products`
  )
}

export function createProductLabelConfig(data: Partial<ProductLabelConfig>) {
  return request.post<ProductLabelConfig>(BASE, data)
}

export function updateProductLabelConfig(id: number, data: Partial<ProductLabelConfig>) {
  return request.put<ProductLabelConfig>(`${BASE}/${id}`, data)
}

export function deleteProductLabelConfig(id: number) {
  return request.delete<{ message: string }>(`${BASE}/${id}`)
}

export interface ProductLabelPrefill {
  product_cd: string
  master_product_name: string
  product_alias?: string | null
  route_cd?: string | null
  lot_size?: number | null
  unit_per_box?: number | null
  label_product_name: string
  process_unit_qty: number | null
  process_slots: (string | null)[]
  paper_color: string
  product_name_color: string
  supply_type: string
  route_description?: string
  remark?: string | null
}

export function fetchProductLabelPrefill(productCd: string) {
  return request.get<{ success?: boolean; data?: ProductLabelPrefill }>(
    `${BASE}/prefill/${encodeURIComponent(productCd)}`
  )
}

export function syncProductLabelFromMaster() {
  return request.post<{ success?: boolean; data?: { added: number; total_products: number } }>(
    `${BASE}/sync-from-master`
  )
}

export function importProductLabelFromMaster(productCd: string) {
  return request.post<ProductLabelConfig>(
    `${BASE}/by-product/${encodeURIComponent(productCd)}/import-from-master`
  )
}

export function deriveProductLabelProcesses(productCd: string) {
  return request.post<ProductLabelConfig | { product_cd: string; process_slots: (string | null)[] }>(
    `${BASE}/by-product/${encodeURIComponent(productCd)}/derive-processes`
  )
}

export function deriveAllProductLabelProcesses() {
  return request.post<{
    success?: boolean
    data?: { updated: number; skipped: number; upper_preserved: number; total: number }
  }>(`${BASE}/derive-processes-all`)
}

export interface OutsourceOrderEmailItem {
  product_cd: string
  order_qty: number
  label_product_name?: string | null
  master_product_name?: string | null
  process_unit_qty?: number | null
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
  items: ProductLabelConfig[]
  email_enabled: boolean
  smtp_configured: boolean
  template_subject?: string | null
  can_send: boolean
}

export function fetchOutsourceLabelOrders() {
  return request.get<{ list: ProductLabelConfig[]; total: number }>(`${BASE}/outsource-orders`)
}

export function fetchOutsourceOrderEmailPreview() {
  return request.get<OutsourceOrderEmailPreview>(`${BASE}/outsource-order/email-preview`)
}

export function sendOutsourceOrderEmail(data: {
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

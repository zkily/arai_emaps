/**
 * 検査新聞紙通知 API（品質管理）
 * 切断実績確定後、対象製品があれば検査工程へ「新聞紙を入れる」自動メールを送信する。
 */
import request from '@/shared/api/request'

export const INSPECTION_NEWSPAPER_EVENT = 'INSPECTION_NEWSPAPER_ALERT'

const BASE = '/api/quality/inspection-newspaper'

export interface InspectionNewspaperProduct {
  id: number
  product_cd: string
  product_name: string | null
  updated_by: string | null
  created_at: string | null
  updated_at: string | null
}

export interface InspectionNewspaperSetting {
  event_code: string
  event_name: string
  is_active: boolean
  email_enabled: boolean
}

export interface InspectionNewspaperMatchedRow {
  product_cd: string
  product_name: string
  batch_key: string
  cutting_machine: string | null
  quantity: number
  already_sent: boolean
  delivered_count?: number
  reference_key?: string
}

export interface InspectionNewspaperPreview {
  success: boolean
  production_day: string
  enabled: boolean
  smtp_configured: boolean
  template_subject: string | null
  matched_rows: InspectionNewspaperMatchedRow[]
  matched_count: number
  pending_count: number
  product_count: number
  total_quantity: number
  recipients: Array<{ email: string; name: string; source: string }>
  recipient_count: number
  already_sent: boolean
  can_send: boolean
}

export interface InspectionNewspaperSendResult {
  success: boolean
  data: {
    success: boolean
    skipped: boolean
    reason?: string
    sent_count: number
    failed?: Array<{ email: string; error: string }>
    message?: string
  }
  message?: string
}

export interface InspectionNewspaperHistoryItem {
  id: number
  reference_key: string
  recipient_email: string
  subject: string | null
  status: 'success' | 'failed'
  error_message: string | null
  sent_at: string | null
}

export function getInspectionNewspaperProducts() {
  return request.get(`${BASE}/products`) as unknown as Promise<{
    success: boolean
    data: { list: InspectionNewspaperProduct[] }
  }>
}

export function addInspectionNewspaperProduct(data: {
  product_cd: string
  product_name?: string | null
}) {
  return request.post(`${BASE}/products`, data) as unknown as Promise<{ success: boolean }>
}

export function deleteInspectionNewspaperProduct(id: number) {
  return request.delete(`${BASE}/products/${id}`) as unknown as Promise<{ success: boolean }>
}

export function getInspectionNewspaperSetting() {
  return request.get(`${BASE}/setting`) as unknown as Promise<{
    success: boolean
    data: InspectionNewspaperSetting
  }>
}

export function updateInspectionNewspaperSetting(data: {
  is_active?: boolean
  email_enabled?: boolean
}) {
  return request.put(`${BASE}/setting`, data) as unknown as Promise<{
    success: boolean
    data: { is_active: boolean; email_enabled: boolean }
  }>
}

export function getInspectionNewspaperPreview(productionDay: string) {
  return request.get(`${BASE}/preview`, {
    params: { production_day: productionDay },
  }) as unknown as Promise<InspectionNewspaperPreview>
}

export function sendInspectionNewspaperNotification(productionDay: string, force = false) {
  return request.post(`${BASE}/send`, null, {
    params: { production_day: productionDay, force },
  }) as unknown as Promise<InspectionNewspaperSendResult>
}

export function getInspectionNewspaperHistory(limit = 50) {
  return request.get(`${BASE}/history`, {
    params: { limit },
  }) as unknown as Promise<{
    success: boolean
    data: { list: InspectionNewspaperHistoryItem[] }
  }>
}

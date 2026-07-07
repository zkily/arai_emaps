/**
 * 大量廃棄・保留品記録 API
 */
import request from '@/utils/request'

const BASE_URL = '/api/erp/bulk-disposal-retention'

export interface BulkDisposalRetentionRecord {
  id: number
  occurred_date: string
  report_category: string
  process_name: string
  product_cd?: string | null
  product_name: string
  quantity: number
  handling_status: '未処理' | '処理済'
  processed_date?: string | null
  processing_deadline_date?: string | null
  is_overdue?: boolean
  management_no?: string | null
  remarks?: string | null
  created_by_user_id?: number | null
  updated_by_user_id?: number | null
  created_at?: string | null
  updated_at?: string | null
}

export interface BulkDisposalRetentionQuery {
  page?: number
  page_size?: number
  occurred_date_from?: string
  occurred_date_to?: string
  report_category?: string
  process_name?: string
  handling_status?: string
  product_cd?: string
  keyword?: string
  overdue_only?: boolean
}

export interface BulkDisposalRetentionListResponse {
  list: BulkDisposalRetentionRecord[]
  total: number
  pending_total: number
  overdue_total?: number
  page: number
  page_size: number
}

export interface BulkDisposalRetentionForm {
  occurred_date: string
  report_category: string
  process_name: string
  product_cd?: string
  product_name: string
  quantity: number
  handling_status: string
  processed_date?: string | null
  processing_deadline_date?: string | null
  management_no?: string
  remarks?: string
}

export interface BulkDisposalRetentionOptions {
  report_categories: string[]
  process_names: string[]
  handling_statuses: string[]
}

export interface BulkDisposalRetentionNotifyPreview {
  success: boolean
  item_count: number
  total_quantity: number
  overdue_count?: number
  has_deadline_notice?: boolean
  items: BulkDisposalRetentionRecord[]
  email_enabled: boolean
  smtp_configured: boolean
  template_subject?: string | null
  can_send: boolean
}

export interface BulkDisposalRetentionNotifySendParams {
  user_ids: number[]
  record_ids?: number[]
}

export interface BulkDisposalRetentionNotifySendResult {
  success: boolean
  message: string
  item_count: number
  total_quantity: string
  email_sent_count: number
  email_failed: Array<{ email: string; error: string }>
  recipient_count: number
}

export interface BulkDisposalRetentionOverdueSummary {
  as_of: string
  count: number
  list: Array<{
    id: number
    product_name: string
    product_cd?: string | null
    management_no?: string | null
    processing_deadline_date?: string | null
    occurred_date?: string | null
    quantity: number
  }>
}

export function getBulkDisposalRetentionOverdueSummary() {
  return request.get<BulkDisposalRetentionOverdueSummary>(`${BASE_URL}/overdue-summary`)
}

export function getBulkDisposalRetentionOptions() {
  return request.get<BulkDisposalRetentionOptions>(`${BASE_URL}/options`)
}

export function getBulkDisposalRetentionList(params?: BulkDisposalRetentionQuery) {
  return request.get<BulkDisposalRetentionListResponse>(BASE_URL, { params })
}

export function createBulkDisposalRetention(data: BulkDisposalRetentionForm) {
  return request.post<BulkDisposalRetentionRecord>(BASE_URL, data)
}

export function updateBulkDisposalRetention(id: number, data: BulkDisposalRetentionForm) {
  return request.put<BulkDisposalRetentionRecord>(`${BASE_URL}/${id}`, data)
}

export function deleteBulkDisposalRetention(id: number) {
  return request.delete(`${BASE_URL}/${id}`)
}

export function previewBulkDisposalRetentionNotification(params?: { record_ids?: string }) {
  return request.get<BulkDisposalRetentionNotifyPreview>(`${BASE_URL}/notify/preview`, { params })
}

export function sendBulkDisposalRetentionNotification(data: BulkDisposalRetentionNotifySendParams) {
  return request.post<BulkDisposalRetentionNotifySendResult>(`${BASE_URL}/notify/send`, data)
}

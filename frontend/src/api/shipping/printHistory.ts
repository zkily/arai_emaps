/**
 * 印刷履歴 API（出荷報告・カレンダー等）
 */
import request from '@/utils/request'

export interface RecordPrintHistoryParams {
  report_type: string
  report_title?: string
  filters?: Record<string, unknown>
  record_count?: number
  status?: string
  error_message?: string
}

export interface GetPrintHistoryParams {
  report_type?: string
  user_name?: string
  date_from?: string
  date_to?: string
  page?: number
  limit?: number
}

export function getPrintHistory(params?: GetPrintHistoryParams) {
  const { page = 1, limit = 100, ...rest } = params || {}
  const offset = (page - 1) * limit
  return request.get('/api/shipping/print/history', { params: { ...rest, limit, offset } })
}

export function recordPrintHistory(params: RecordPrintHistoryParams) {
  return request.post('/api/shipping/print/history', params)
}

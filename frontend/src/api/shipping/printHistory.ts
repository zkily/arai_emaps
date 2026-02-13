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

export function recordPrintHistory(params: RecordPrintHistoryParams) {
  return request.post('/api/shipping/print/history', params)
}

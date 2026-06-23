/**
 * レポート配信 API（/api/reports/*）
 * 報告定義・プレビュー・手動送信・スケジュール・送信履歴
 */
import request from '@/shared/api/request'

const BASE = '/api/reports'

export interface ReportParameterField {
  key: string
  label: string
  type: string
  default?: string
  presets?: string[]
}

export interface ReportParameterSchema {
  fields?: ReportParameterField[]
}

export interface ReportDefinition {
  id: number
  report_code: string
  report_name: string
  category: string
  default_format: string
  parameter_schema?: ReportParameterSchema | null
  event_code: string
  description?: string | null
  is_active: boolean
}

export interface ReportRecipient {
  email?: string
  line_user_id?: string
  name: string
  source: string
}

export interface ReportPreview {
  success: boolean
  report_code: string
  report_name: string
  format: string
  period_label: string
  record_count: number
  summary_html: string
  attachments: { filename: string; size: number }[]
  email_enabled: boolean
  line_enabled: boolean
  smtp_configured: boolean
  line_configured: boolean
  template_subject?: string | null
  recipients: ReportRecipient[]
  line_recipients: ReportRecipient[]
  recipient_count: number
  line_recipient_count: number
  can_send_email: boolean
  can_send_line: boolean
  can_send: boolean
}

export interface ReportSendResult {
  success: boolean
  status: string
  trigger?: string
  report_code?: string
  period_label?: string
  total_sent?: number
  email_sent_count?: number
  line_sent_count?: number
  message: string
}

export interface ReportSchedule {
  id: number
  report_code: string
  schedule_type: string
  schedule_time: string
  schedule_config?: Record<string, unknown> | null
  parameters?: Record<string, unknown> | null
  format?: string | null
  is_active: boolean
  last_run_at?: string | null
  next_run_at?: string | null
  created_at?: string | null
}

export interface ReportSendLog {
  id: number
  report_code: string
  trigger_type: string
  reference_key: string
  file_name?: string | null
  file_size?: number | null
  recipient_count: number
  success_count: number
  status: string
  message?: string | null
  error_message?: string | null
  triggered_by?: number | null
  created_at?: string | null
}

export function fetchReportDefinitions(): Promise<ReportDefinition[]> {
  return request.get(`${BASE}/definitions`) as unknown as Promise<ReportDefinition[]>
}

export function previewReport(
  reportCode: string,
  parameters: Record<string, unknown>,
): Promise<ReportPreview> {
  return request.post(`${BASE}/${reportCode}/preview`, { parameters }) as unknown as Promise<ReportPreview>
}

export function sendReport(
  reportCode: string,
  parameters: Record<string, unknown>,
  format?: string | null,
): Promise<ReportSendResult> {
  return request.post(`${BASE}/${reportCode}/send`, { parameters, format }) as unknown as Promise<ReportSendResult>
}

/** 添付ファイルをブラウザでダウンロードする（手動確認用） */
export async function downloadReport(
  reportCode: string,
  parameters: Record<string, unknown>,
  format?: string | null,
): Promise<void> {
  const resp = (await request.post(
    `${BASE}/${reportCode}/download`,
    { parameters, format },
    { responseType: 'blob' },
  )) as unknown as Blob
  const ext = format === 'pdf' ? 'pdf' : 'xlsx'
  const url = window.URL.createObjectURL(resp)
  const a = document.createElement('a')
  a.href = url
  a.download = `${reportCode}.${ext}`
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

export function fetchReportSchedules(reportCode?: string): Promise<ReportSchedule[]> {
  return request.get(`${BASE}/schedules`, {
    params: reportCode ? { report_code: reportCode } : {},
  }) as unknown as Promise<ReportSchedule[]>
}

export function createReportSchedule(body: Partial<ReportSchedule>): Promise<ReportSchedule> {
  return request.post(`${BASE}/schedules`, body) as unknown as Promise<ReportSchedule>
}

export function updateReportSchedule(
  id: number,
  body: Partial<ReportSchedule>,
): Promise<ReportSchedule> {
  return request.put(`${BASE}/schedules/${id}`, body) as unknown as Promise<ReportSchedule>
}

export function deleteReportSchedule(id: number): Promise<{ success: boolean }> {
  return request.delete(`${BASE}/schedules/${id}`) as unknown as Promise<{ success: boolean }>
}

export interface ReportSendLogResponse {
  success: boolean
  data: ReportSendLog[]
  page: number
  limit: number
}

export function fetchReportSendLogs(params: {
  report_code?: string
  page?: number
  limit?: number
}): Promise<ReportSendLogResponse> {
  return request.get(`${BASE}/send-logs`, { params }) as unknown as Promise<ReportSendLogResponse>
}

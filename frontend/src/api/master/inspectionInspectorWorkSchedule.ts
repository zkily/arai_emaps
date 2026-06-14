import request from '@/utils/request'

export type InspectorWorkScheduleRuleKind = 'date' | 'time'

export interface InspectionInspectorWorkScheduleItem {
  id: number
  inspector_user_id: number
  inspector_name?: string | null
  rule_kind: InspectorWorkScheduleRuleKind
  rule_kind_label?: string
  schedule_date?: string | null
  weekday?: number | null
  weekday_label?: string | null
  target_label?: string | null
  work_start_time?: string | null
  work_end_time?: string | null
  time_range_label?: string | null
  scheduled_hours: number
  note?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface WeekdayOption {
  value: number
  label: string
}

export interface RuleKindOption {
  value: InspectorWorkScheduleRuleKind
  label: string
}

export function fetchInspectionInspectorWorkSchedules(params?: {
  inspector_user_id?: number
  start_date?: string
  end_date?: string
}): Promise<{
  success?: boolean
  data?: { items: InspectionInspectorWorkScheduleItem[]; total: number }
}> {
  return request.get('/api/master/inspection-inspector-work-schedule', { params }) as Promise<{
    success?: boolean
    data?: { items: InspectionInspectorWorkScheduleItem[]; total: number }
  }>
}

export function fetchInspectionInspectorWorkScheduleWeekdays(): Promise<WeekdayOption[]> {
  return request.get('/api/master/inspection-inspector-work-schedule/weekdays') as Promise<WeekdayOption[]>
}

export function fetchInspectionInspectorWorkScheduleRuleKinds(): Promise<RuleKindOption[]> {
  return request.get('/api/master/inspection-inspector-work-schedule/rule-kinds') as Promise<RuleKindOption[]>
}

export function fetchInspectionInspectorWorkScheduleDefaults(): Promise<{
  success?: boolean
  data?: {
    default_scheduled_hours: number
    default_work_start_time: string
    default_work_end_time: string
    priority: string[]
  }
}> {
  return request.get('/api/master/inspection-inspector-work-schedule/defaults') as Promise<{
    success?: boolean
    data?: {
      default_scheduled_hours: number
      default_work_start_time: string
      default_work_end_time: string
      priority: string[]
    }
  }>
}

export function batchCreateInspectionInspectorWorkSchedules(body: {
  inspector_user_ids: number[]
  rule_kind: InspectorWorkScheduleRuleKind
  schedule_date?: string
  weekday?: number
  work_start_time: string
  work_end_time: string
  scheduled_hours?: number
  note?: string
}): Promise<{
  success?: boolean
  created?: number
  skipped?: number
  failed?: number
  skipped_inspector_names?: string[]
  message?: string
}> {
  return request.post('/api/master/inspection-inspector-work-schedule/batch', body) as Promise<{
    success?: boolean
    created?: number
    skipped?: number
    failed?: number
    skipped_inspector_names?: string[]
    message?: string
  }>
}

export function createInspectionInspectorWorkSchedule(body: {
  inspector_user_id: number
  rule_kind: InspectorWorkScheduleRuleKind
  schedule_date?: string
  weekday?: number
  work_start_time: string
  work_end_time: string
  scheduled_hours?: number
  note?: string
}): Promise<{ success?: boolean; data?: InspectionInspectorWorkScheduleItem; message?: string }> {
  return request.post('/api/master/inspection-inspector-work-schedule', body) as Promise<{
    success?: boolean
    data?: InspectionInspectorWorkScheduleItem
    message?: string
  }>
}

export function updateInspectionInspectorWorkSchedule(
  id: number,
  body: { work_start_time?: string; work_end_time?: string; scheduled_hours?: number; note?: string },
): Promise<{ success?: boolean; data?: InspectionInspectorWorkScheduleItem; message?: string }> {
  return request.put(`/api/master/inspection-inspector-work-schedule/${id}`, body) as Promise<{
    success?: boolean
    data?: InspectionInspectorWorkScheduleItem
    message?: string
  }>
}

export function deleteInspectionInspectorWorkSchedule(id: number): Promise<{ success?: boolean }> {
  return request.delete(`/api/master/inspection-inspector-work-schedule/${id}`) as Promise<{ success?: boolean }>
}

export function hoursFromTimeRange(start?: string | null, end?: string | null): number {
  if (!start || !end) return 0
  const [sh, sm] = start.split(':').map((v) => Number(v))
  const [eh, em] = end.split(':').map((v) => Number(v))
  if ([sh, sm, eh, em].some((v) => Number.isNaN(v))) return 0
  let startMins = sh * 60 + sm
  let endMins = eh * 60 + em
  if (endMins <= startMins) endMins += 24 * 60
  return Math.round(((endMins - startMins) / 60) * 10) / 10
}

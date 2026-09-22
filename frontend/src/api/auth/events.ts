import request from '@/shared/api/request'

export type UserEventColor = 'blue' | 'green' | 'amber' | 'rose' | 'slate' | 'violet' | 'cyan'
export type UserEventRecurrence = 'none' | 'daily' | 'weekly' | 'monthly' | 'yearly'
export type UserEventVisibility = 'self' | 'department' | 'all'
export type UserEventViewerScope = 'self' | 'department' | 'all'
export type UserEventEditScope = 'this' | 'following' | 'all'

export interface UserEventItem {
  id: number
  title: string
  description: string | null
  location: string | null
  start_at: string
  end_at: string
  all_day: boolean
  color: UserEventColor
  visibility: UserEventVisibility
  recurrence_rule: UserEventRecurrence | null
  recurrence_until: string | null
  remind_offset_minutes: number | null
  remind_at: string | null
  reminded_at: string | null
  occurrence_date: string | null
  owner_id: number | null
  owner_name: string | null
  department_id: number | null
  department_name: string | null
  is_owner: boolean
  created_at: string | null
  updated_at: string | null
}

export interface UserEventListResponse {
  list: UserEventItem[]
  viewer_scope: UserEventViewerScope
}

export interface UserEventUpcomingResponse {
  due_now: UserEventItem[]
  badge_count: number
  today_count: number
  week_count: number
}

export interface UserEventCreatePayload {
  title: string
  start_at: string
  end_at: string
  description?: string | null
  location?: string | null
  all_day?: boolean
  color?: UserEventColor | null
  visibility?: UserEventVisibility | null
  recurrence_rule?: UserEventRecurrence | null
  recurrence_until?: string | null
  remind_offset_minutes?: number | null
}

export interface UserEventUpdatePayload extends Partial<UserEventCreatePayload> {
  edit_scope?: UserEventEditScope
  occurrence_date?: string | null
}

export interface UserEventReschedulePayload {
  start_at: string
  end_at: string
  edit_scope?: UserEventEditScope
  occurrence_date?: string | null
}

export const getUserEvents = (from: string, to: string) => {
  return request.get<any, UserEventListResponse>('/api/auth/events', { params: { from, to } })
}

export const getUserEventsUpcoming = () => {
  return request.get<any, UserEventUpcomingResponse>('/api/auth/events/upcoming')
}

export const createUserEvent = (payload: UserEventCreatePayload) => {
  return request.post<any, UserEventItem>('/api/auth/events', payload)
}

export const updateUserEvent = (id: number, payload: UserEventUpdatePayload) => {
  return request.patch<any, UserEventItem>(`/api/auth/events/${id}`, payload)
}

export const rescheduleUserEvent = (id: number, payload: UserEventReschedulePayload) => {
  return request.patch<any, UserEventItem>(`/api/auth/events/${id}/reschedule`, payload)
}

export const ackUserEventReminder = (id: number, occurrenceDate?: string | null) => {
  return request.post<any, UserEventItem>(`/api/auth/events/${id}/ack-reminder`, null, {
    params: occurrenceDate ? { occurrence_date: occurrenceDate } : undefined,
  })
}

export const deleteUserEvent = (
  id: number,
  opts?: { edit_scope?: UserEventEditScope; occurrence_date?: string | null },
) => {
  return request.delete(`/api/auth/events/${id}`, {
    params: {
      edit_scope: opts?.edit_scope || 'all',
      ...(opts?.occurrence_date ? { occurrence_date: opts.occurrence_date } : {}),
    },
  })
}

export const VISIBILITY_OPTIONS: UserEventVisibility[] = ['self', 'department', 'all']

export const EVENT_COLORS: UserEventColor[] = [
  'blue',
  'green',
  'amber',
  'rose',
  'slate',
  'violet',
  'cyan',
]

export const RECURRENCE_OPTIONS: UserEventRecurrence[] = [
  'none',
  'daily',
  'weekly',
  'monthly',
  'yearly',
]

export const REMIND_OFFSET_OPTIONS = [0, 5, 10, 15, 30, 60, 120, 1440] as const

export function eventDurationMinutes(ev: Pick<UserEventItem, 'start_at' | 'end_at' | 'all_day'>) {
  if (ev.all_day) return 24 * 60
  const start = new Date(ev.start_at.replace(' ', 'T'))
  const end = new Date(ev.end_at.replace(' ', 'T'))
  const mins = Math.round((end.getTime() - start.getTime()) / 60000)
  return Math.max(15, mins)
}

export function isRecurringOccurrence(ev: Pick<UserEventItem, 'recurrence_rule' | 'occurrence_date'>) {
  return !!(ev.recurrence_rule && ev.occurrence_date)
}

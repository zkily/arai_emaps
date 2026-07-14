import request from '@/shared/api/request'

export type UserMemoColor = 'blue' | 'green' | 'amber' | 'rose' | 'slate'

export interface UserMemoItem {
  id: number
  title: string
  content: string | null
  memo_date: string
  memo_time: string | null
  remind_at: string | null
  remind_offset_minutes: number | null
  color: UserMemoColor | null
  status: number
  reminded_at: string | null
  created_at: string
  updated_at: string
}

export interface UserMemoListResponse {
  list: UserMemoItem[]
}

export interface UserMemoUpcomingResponse {
  due_now: UserMemoItem[]
  badge_count: number
}

export interface UserMemoCreatePayload {
  title: string
  memo_date: string
  content?: string | null
  memo_time?: string | null
  all_day?: boolean
  remind_offset_minutes?: number | null
  color?: UserMemoColor | null
}

export interface UserMemoUpdatePayload {
  title?: string
  content?: string | null
  memo_date?: string
  memo_time?: string | null
  all_day?: boolean
  remind_offset_minutes?: number | null
  color?: UserMemoColor | null
  status?: number
}

export const getUserMemos = (from: string, to: string) => {
  return request.get<any, UserMemoListResponse>('/api/auth/memos', { params: { from, to } })
}

export const getUserMemosUpcoming = () => {
  return request.get<any, UserMemoUpcomingResponse>('/api/auth/memos/upcoming')
}

export const createUserMemo = (payload: UserMemoCreatePayload) => {
  return request.post<any, UserMemoItem>('/api/auth/memos', payload)
}

export const updateUserMemo = (id: number, payload: UserMemoUpdatePayload) => {
  return request.patch<any, UserMemoItem>(`/api/auth/memos/${id}`, payload)
}

export const completeUserMemo = (id: number) => {
  return request.post<any, UserMemoItem>(`/api/auth/memos/${id}/complete`)
}

export const ackUserMemoReminder = (id: number) => {
  return request.post<any, UserMemoItem>(`/api/auth/memos/${id}/ack-reminder`)
}

export const deleteUserMemo = (id: number) => {
  return request.delete(`/api/auth/memos/${id}`)
}

export const MEMO_COLORS: UserMemoColor[] = ['blue', 'green', 'amber', 'rose', 'slate']

export const REMIND_OFFSET_OPTIONS = [0, 5, 15, 30] as const

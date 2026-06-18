import request from '@/shared/api/request'

export interface ShortcutItem {
  path: string
  menu_code?: string | null
  visit_count?: number | null
  last_visited_at?: string | null
}

export interface ShortcutsResponse {
  pinned: ShortcutItem[]
  frequent: ShortcutItem[]
}

export const getShortcuts = () => {
  return request.get<any, ShortcutsResponse>('/api/auth/shortcuts')
}

export const updatePins = (paths: string[]) => {
  return request.put<any, ShortcutsResponse>('/api/auth/shortcuts/pins', { paths })
}

export const recordPageVisit = (path: string) => {
  return request.post('/api/auth/shortcuts/visit', { path })
}

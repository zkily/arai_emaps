import request from '@/utils/request'

export interface LongStayUninspectedRow {
  id: number
  product_name: string
  quantity: number
  sort_order: number
  created_at?: string | null
  updated_at?: string | null
}

export interface LongStayUninspectedPayload {
  product_name: string
  quantity: number
  sort_order?: number | null
}

const BASE = '/api/shipping/long-stay-uninspected'

export function listLongStayUninspected() {
  return request.get<{ success?: boolean; data: LongStayUninspectedRow[] }>(BASE)
}

export function createLongStayUninspected(body: LongStayUninspectedPayload) {
  return request.post<{ success?: boolean; id?: number }>(BASE, body)
}

export function updateLongStayUninspected(id: number, body: LongStayUninspectedPayload) {
  return request.put<{ success?: boolean }>(`${BASE}/${id}`, body)
}

export function deleteLongStayUninspected(id: number) {
  return request.delete<{ success?: boolean }>(`${BASE}/${id}`)
}

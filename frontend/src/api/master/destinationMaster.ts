/**
 * 納入先マスタ API
 */
import request from '@/shared/api/request'
import type { DestinationItem, DestinationHolidayItem, DestinationWorkdayItem } from '@/types/master'

export interface DestinationListParams {
  keyword?: string
  status?: number
  issue_type?: string
  carrier_cd?: string
  page?: number
  pageSize?: number
}

export interface DestinationListResponse {
  success?: boolean
  data?: { list: DestinationItem[]; total: number }
  list?: DestinationItem[]
  total?: number
}

/** 納入先一覧取得 */
export function getDestinationList(params: DestinationListParams = {}): Promise<DestinationListResponse> {
  return request.get('/api/master/destinations', { params }) as Promise<DestinationListResponse>
}

/** 納入先オプション（有効のみ） */
export function getDestinationOptions(): Promise<{ cd: string; name: string }[]> {
  return request.get('/api/master/destinations/options') as Promise<{ cd: string; name: string }[]>
}

/** 納入先1件取得 */
export function getDestinationById(id: number): Promise<DestinationItem> {
  return request.get(`/api/master/destinations/${id}`) as Promise<DestinationItem>
}

/** 納入先新規登録 */
export function createDestination(data: Partial<DestinationItem>): Promise<DestinationItem> {
  return request.post('/api/master/destinations', data) as Promise<DestinationItem>
}

/** 納入先更新 */
export function updateDestination(data: Partial<DestinationItem> & { id: number }): Promise<DestinationItem> {
  return request.put(`/api/master/destinations/${data.id}`, data) as Promise<DestinationItem>
}

/** 納入先状態更新 */
export function updateDestinationStatus(id: number, status: number): Promise<DestinationItem> {
  return request.patch(`/api/master/destinations/${id}/status?status=${status}`) as Promise<DestinationItem>
}

/** 納入先削除 */
export function deleteDestinationById(id: number): Promise<{ message: string }> {
  return request.delete(`/api/master/destinations/${id}`) as Promise<{ message: string }>
}

/** 指定納入先の休日一覧 */
export function getHolidaysByDest(destinationCd: string): Promise<DestinationHolidayItem[]> {
  return request.get(
    `/api/master/destinations/holidays/by-destination/${encodeURIComponent(destinationCd)}`
  ) as Promise<DestinationHolidayItem[]>
}

/** 休日追加 */
export function addHolidayDate(destinationCd: string, holidayDate: string): Promise<DestinationHolidayItem> {
  return request.post('/api/master/destinations/holidays', null, {
    params: { destinationCd, holidayDate },
  }) as Promise<DestinationHolidayItem>
}

/** 休日削除 */
export function deleteHolidayDate(holidayId: number): Promise<{ message: string }> {
  return request.delete(`/api/master/destinations/holidays/${holidayId}`) as Promise<{ message: string }>
}

/** 指定納入先の臨時出勤日一覧 */
export function getWorkdaysByDest(destinationCd: string): Promise<DestinationWorkdayItem[]> {
  return request.get(
    `/api/master/destinations/workdays/by-destination/${encodeURIComponent(destinationCd)}`
  ) as Promise<DestinationWorkdayItem[]>
}

/** 臨時出勤日追加 */
export function addWorkdayDate(
  destinationCd: string,
  workDate: string,
  reason?: string
): Promise<DestinationWorkdayItem> {
  return request.post('/api/master/destinations/workdays', null, {
    params: { destinationCd, workDate, reason },
  }) as Promise<DestinationWorkdayItem>
}

/** 臨時出勤日削除 */
export function deleteWorkdayDate(workdayId: number): Promise<{ message: string }> {
  return request.delete(`/api/master/destinations/workdays/${workdayId}`) as Promise<{ message: string }>
}

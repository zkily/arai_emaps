/**
 * 工程ルートマスタ API
 */
import request from '@/shared/api/request'
import type { RouteItem, RouteStepItem } from '@/types/master'

export interface RouteListParams {
  keyword?: string
  page?: number
  pageSize?: number
}

export interface RouteListResponse {
  success?: boolean
  data?: { list: RouteItem[]; total: number }
  list?: RouteItem[]
  total?: number
}

/** ルート一覧取得 */
export function fetchRoutes(
  keyword: string = '',
  page: number = 1,
  pageSize: number = 50
): Promise<RouteListResponse> {
  return request.get('/api/master/process-routes', {
    params: { keyword: keyword || undefined, page, pageSize },
  }) as Promise<RouteListResponse>
}

/** ルートCDで1件取得（ステップ編集画面用） */
export function getRouteInfo(routeCd: string): Promise<RouteItem> {
  return request.get(`/api/master/process-routes/by-cd/${encodeURIComponent(routeCd)}`) as Promise<RouteItem>
}

/** ルートIDで1件取得 */
export function getRouteById(routeId: number): Promise<RouteItem> {
  return request.get(`/api/master/process-routes/${routeId}`) as Promise<RouteItem>
}

/** ルート新規登録 */
export function createRoute(data: Partial<RouteItem>): Promise<RouteItem> {
  return request.post('/api/master/process-routes', data) as Promise<RouteItem>
}

/** ルート更新 */
export function updateRoute(id: number, data: Partial<RouteItem>): Promise<RouteItem> {
  return request.put(`/api/master/process-routes/${id}`, data) as Promise<RouteItem>
}

/** ルート削除 */
export function deleteRoute(id: number): Promise<{ message: string }> {
  return request.delete(`/api/master/process-routes/${id}`) as Promise<{ message: string }>
}

/** ルートのステップ一覧取得 */
export function getRouteSteps(routeCd: string): Promise<RouteStepItem[]> {
  return request.get(
    `/api/master/process-routes/by-cd/${encodeURIComponent(routeCd)}/steps`
  ) as Promise<RouteStepItem[]>
}

/** ステップ順序一括更新 */
export function updateStepOrder(
  routeCd: string,
  orderData: Array<{ id: number; step_no: number }>
): Promise<{ message: string }> {
  return request.put(
    `/api/master/process-routes/by-cd/${encodeURIComponent(routeCd)}/steps/order`,
    orderData
  ) as Promise<{ message: string }>
}

/** ステップ追加 */
export function createRouteStep(routeCd: string, data: Partial<RouteStepItem>): Promise<RouteStepItem> {
  return request.post(
    `/api/master/process-routes/by-cd/${encodeURIComponent(routeCd)}/steps`,
    data
  ) as Promise<RouteStepItem>
}

/** ステップ更新 */
export function updateRouteStep(stepId: number, data: Partial<RouteStepItem>): Promise<RouteStepItem> {
  return request.put(`/api/master/process-routes/steps/${stepId}`, data) as Promise<RouteStepItem>
}

/** ステップ削除 */
export function deleteRouteStep(routeCd: string, stepId: number): Promise<{ message: string }> {
  return request.delete(
    `/api/master/process-routes/by-cd/${encodeURIComponent(routeCd)}/steps/${stepId}`
  ) as Promise<{ message: string }>
}

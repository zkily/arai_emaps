/**
 * FIN（経理・原価・人事）API クライアント。
 * バックエンドの汎用 CRUD（/api/fin/<domain>/<resource>）に対応する
 * リソースファクトリ。FIN 汎用コンポーネント（views/fin/components）が利用する。
 */
import request from '@/shared/api/request'
import type { FinPage } from '@/views/fin/components/types'

export interface FinListParams {
  page?: number
  page_size?: number
  q?: string
  order_by?: string
  [key: string]: unknown
}

export interface FinResource<T = Record<string, unknown>> {
  list(params?: FinListParams): Promise<FinPage<T>>
  get(id: number | string): Promise<T>
  create(payload: Partial<T>): Promise<T>
  update(id: number | string, payload: Partial<T>): Promise<T>
  remove(id: number | string): Promise<{ message: string; id: number }>
}

type Removed = { message: string; id: number }

/**
 * apiBase（例: /api/fin/accounting/journal-entry）から CRUD クライアントを生成。
 * request のレスポンスインターセプタが response.data を返すため、axios の第2型引数 R を
 * データ型に揃えて Promise<データ> として型付けする。
 */
export function createFinResource<T = Record<string, unknown>>(apiBase: string): FinResource<T> {
  return {
    list: (params = {}) => request.get<FinPage<T>, FinPage<T>>(apiBase, { params }),
    get: (id) => request.get<T, T>(`${apiBase}/${id}`),
    create: (payload) => request.post<T, T>(apiBase, payload),
    update: (id, payload) => request.put<T, T>(`${apiBase}/${id}`, payload),
    remove: (id) => request.delete<Removed, Removed>(`${apiBase}/${id}`),
  }
}

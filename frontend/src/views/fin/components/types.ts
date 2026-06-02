/**
 * FIN 汎用コンポーネント共通型。
 * 生成ラッパ（views/fin/**）から渡される列・フィールド・カード定義。
 */
export interface FinColumn {
  prop: string
  label: string
  width?: number
  align?: 'left' | 'center' | 'right'
}

export type FinFieldType = 'text' | 'number' | 'date' | 'datetime' | 'switch' | 'textarea'

export interface FinField {
  prop: string
  label: string
  type: FinFieldType
  required?: boolean
}

export interface FinHomeCard {
  title: string
  desc?: string
  path: string
  icon?: string
}

/** バックエンド汎用 CRUD のページングレスポンス。 */
export interface FinPage<T = Record<string, unknown>> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

/**
 * 製品工程ガント API
 */
import request from '@/utils/request'

const BASE = '/api/database/product-process-gantt'

export interface GanttDayCell {
  /** 日付 YYYY-MM-DD */
  d: string
  /** 計画数（plan 工程） */
  p?: number
  /** 実績数（plan 工程） */
  a?: number
  /** 在庫数（inventory_trend 工程） */
  i?: number
  /** 倉庫系の推移（inventory_trend 工程の参考値） */
  t?: number
}

export interface TrendDayCell {
  d: string
  v: number
}

export interface GanttRouteStep {
  step_no: number
  process_cd: string
  /** production_summarys 列との対応キー（対応外工程は null） */
  process_key: string | null
  process_name: string
}

export interface GanttProduct {
  product_cd: string
  product_name: string
  route_cd: string
  steps: GanttRouteStep[]
  /** process_key → 日次セル（計画工程は p/a、倉庫系は i/t） */
  days: Record<string, GanttDayCell[]>
  /** process_key → *_trend */
  trends: Record<string, TrendDayCell[]>
  /** process_key → *_actual_plan_trend */
  actual_plan_trends: Record<string, TrendDayCell[]>
}

export type GanttProcessMode = 'plan' | 'plan_actual_merge' | 'inventory_trend'

export interface GanttProcessDef {
  key: string
  label: string
  process_cds: string[]
  mode: GanttProcessMode
  has_trend?: boolean
  has_actual_plan_trend?: boolean
}

export interface ProductProcessGanttData {
  period: { start: string; end: string }
  page: number
  page_size: number
  total: number
  processes: GanttProcessDef[]
  products: GanttProduct[]
}

export interface ProductProcessGanttParams {
  start_date: string
  end_date: string
  /** カンマ区切りで複数指定可 */
  product_cd?: string
  keyword?: string
  page?: number
  page_size?: number
}

export function getProductProcessGantt(params: ProductProcessGanttParams) {
  return request.get<never, { data: ProductProcessGanttData }>(BASE, { params })
}

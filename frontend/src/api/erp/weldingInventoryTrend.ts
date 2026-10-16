/**
 * 溶接品在庫推移 API（/api/erp/production/welding-inventory-trend）
 */
import request from '@/shared/api/request'

const BASE = '/api/erp/production/welding-inventory-trend'

export type WeldingMetricKey =
  | 'forecast'
  | 'molding_actual_plan'
  | 'pre_welding_inventory'
  | 'welding_plan'
  | 'welding_actual'
  | 'welding_inventory'
  | 'welding_trend'
  | 'warehouse_inventory'

export interface WeldingTrendPart {
  part_cd: string
  part_name: string
  stock: Record<string, number>
  planned_usage: Record<string, number>
  has_shortage: boolean
}

export interface WeldingTrendProduct {
  product_cd: string
  product_name: string
  pre_welding_applicable: boolean
  has_shortage: boolean
  metrics: Record<WeldingMetricKey, Record<string, number> | null>
  parts: WeldingTrendPart[]
}

export interface WeldingTrendData {
  date_from: string
  date_to: string
  dates: string[]
  product_count: number
  shortage_count: number
  products: WeldingTrendProduct[]
}

export interface WeldingTrendQuery {
  date_from: string
  date_to: string
  keyword?: string
  part_cd?: string
  shortage_only?: boolean
}

export function fetchWeldingInventoryTrend(
  params: WeldingTrendQuery,
): Promise<{ success: boolean; data: WeldingTrendData }> {
  return request.get(BASE, {
    params: {
      date_from: params.date_from,
      date_to: params.date_to,
      keyword: params.keyword || undefined,
      part_cd: params.part_cd || undefined,
      shortage_only: params.shortage_only || undefined,
    },
    timeout: 120000,
  }) as unknown as Promise<{ success: boolean; data: WeldingTrendData }>
}

export const WELDING_METRICS: Array<{
  key: WeldingMetricKey
  label: string
  mode: 'sum' | 'end'
}> = [
  { key: 'forecast', label: '内示', mode: 'sum' },
  { key: 'molding_actual_plan', label: '成型計画', mode: 'sum' },
  { key: 'pre_welding_inventory', label: '溶接前在庫', mode: 'end' },
  { key: 'welding_plan', label: '溶接計画', mode: 'sum' },
  { key: 'welding_actual', label: '溶接実績', mode: 'sum' },
  { key: 'welding_inventory', label: '溶接在庫', mode: 'end' },
  { key: 'welding_trend', label: '溶接推移', mode: 'end' },
  { key: 'warehouse_inventory', label: '倉庫在庫', mode: 'end' },
]

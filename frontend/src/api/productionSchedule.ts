/**
 * 生産スケジュール・instruction_plans 関連 API
 */
import request from '@/shared/api/request'

export interface MaterialRequirementsSummaryItem {
  material_name: string
  material_manufacturer: string
  standard_specification: string
  /** 期間内・材料グループ別のロット行数（COUNT(*)、start_date ありのみ） */
  piece_count: number
}

export interface MaterialRequirementsSummaryMeta {
  date_start: string
  date_end: string
  production_month_filter: string | null
  total_material_kinds: number
  /** 期間内の対象行合計（piece_count の合計） */
  total_piece_count: number
  effective_date_note: string
  /** 期間が長すぎて日別二次元表を返さないとき true */
  daily_matrix_omitted?: boolean
  daily_matrix_max_days?: number
}

/** 日別×材料（行=材料、列=日付） */
export interface MaterialRequirementsDailyMatrixRow {
  material_name: string
  material_manufacturer: string
  standard_specification: string
  by_date: Record<string, number>
  row_total: number
}

export interface MaterialRequirementsDailyMatrix {
  dates: string[]
  rows: MaterialRequirementsDailyMatrixRow[]
}

export interface MaterialRequirementsSummaryResponse {
  success?: boolean
  message?: string
  data?: {
    items: MaterialRequirementsSummaryItem[]
    summary: MaterialRequirementsSummaryMeta
    daily_matrix: MaterialRequirementsDailyMatrix | null
  }
}

export function fetchMaterialRequirementsSummary(params: {
  date_start: string
  date_end: string
  production_month?: string
}): Promise<MaterialRequirementsSummaryResponse> {
  return request.get('/api/plan/batch/material-requirements-summary', { params })
}

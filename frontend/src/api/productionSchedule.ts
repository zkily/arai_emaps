/**
 * 生産スケジュール・計画関連 API（部品需要量は production_summarys.molding_actual_plan ベース）
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

export interface ComponentRequirementsSummaryItem {
  component_cd: string
  component_name: string
  component_uom: string
  source_lot_count: number
  required_qty: number
}

export interface ComponentRequirementsSummaryMeta {
  date_start: string
  date_end: string
  production_month_filter: string | null
  total_component_kinds: number
  total_required_qty: number
  effective_date_note: string
  daily_matrix_omitted?: boolean
  daily_matrix_max_days?: number
  /** 需求量の駆動列（API） */
  plan_column?: string
}

export interface ComponentRequirementsDailyMatrixRow {
  component_cd: string
  component_name: string
  component_uom: string
  by_date: Record<string, number>
  row_total: number
}

export interface ComponentRequirementsDailyMatrix {
  dates: string[]
  rows: ComponentRequirementsDailyMatrixRow[]
}

export interface ComponentRequirementsSummaryResponse {
  success?: boolean
  message?: string
  data?: {
    items: ComponentRequirementsSummaryItem[]
    summary: ComponentRequirementsSummaryMeta
    daily_matrix: ComponentRequirementsDailyMatrix | null
  }
}

export function fetchComponentRequirementsSummary(params: {
  date_start: string
  date_end: string
  production_month?: string
  /** molding_actual_plan | molding_plan */
  plan_column?: string
}): Promise<ComponentRequirementsSummaryResponse> {
  return request.get('/api/plan/batch/component-requirements-summary', { params })
}

export interface ComponentRequirementsBundleData {
  date_start: string
  date_end: string
  production_month_filter: string | null
  demand: {
    items: ComponentRequirementsSummaryItem[]
    summary: ComponentRequirementsSummaryMeta
    daily_matrix: ComponentRequirementsDailyMatrix | null
  }
  use: {
    items: ComponentRequirementsSummaryItem[]
    summary: ComponentRequirementsSummaryMeta
    daily_matrix: ComponentRequirementsDailyMatrix | null
  }
}

export interface ComponentRequirementsBundleResponse {
  success?: boolean
  message?: string
  data?: ComponentRequirementsBundleData
}

export function fetchComponentRequirementsBundle(params: {
  date_start: string
  date_end: string
  production_month?: string
  plan_column?: string
}): Promise<ComponentRequirementsBundleResponse> {
  return request.get('/api/plan/batch/component-requirements-bundle', { params })
}

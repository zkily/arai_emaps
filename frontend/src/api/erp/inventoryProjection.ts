/**
 * 月末在庫予測 API（/api/inventory-projection/*）
 */
import request from '@/shared/api/request'

const BASE = '/api/inventory-projection'

export interface ProjectionGroup {
  key: string
  name: string
  /** 計画行の代表工程 key（手動修正 API に使用） */
  process_key?: string | null
  /** 日付 ISO → 在庫数（本） */
  daily: Record<string, number>
  /** 有効計画（手動修正の比例配分 > 生計画） */
  plan_daily?: Record<string, number>
  /** 生計画（production_summarys の生データ） */
  plan_auto_daily?: Record<string, number>
  /** 手動修正が適用された日 → 手動合計値 */
  plan_override_daily?: Record<string, number>
  /** 実績 */
  actual_daily?: Record<string, number>
  /** 次工程移動（当該製品ルート上の次工程生産数量） */
  next_usage_daily?: Record<string, number>
  /** 次工程移動の行ラベル（単一行のとき） */
  next_usage_label?: string
  /** 次工程移動の分割行（成型など分岐がある工程） */
  next_usage_rows?: Array<{
    key: string
    label: string
    daily: Record<string, number>
  }> | null
  /** 次工程使用（下流工程の実績→無ければ計画）合計。成型のみ */
  next_consume_daily?: Record<string, number> | null
  /** 次工程使用の行ラベル */
  next_consume_label?: string | null
  /** 次工程使用の分割行（社内メッキ／外注メッキ／溶接／外注溶接） */
  next_consume_rows?: Array<{
    key: string
    label: string
    daily: Record<string, number>
  }> | null
  /** 倉庫グループ内訳: 外注倉庫出荷（外注倉庫ルート製品の内示日別合計） */
  outsourced_warehouse_shipment_daily?: Record<string, number> | null
  /** 月末予測在庫（本） */
  month_end: number
  /** 在庫日数 = 月末在庫 ÷ 翌月日平均内示 */
  days_of_supply: number | null
  next_month_forecast: number
  next_month_workdays: number
}

export interface ProjectionSummaryData {
  year_month: string
  base_date: string
  /** 予測開始日（基準日翌日） */
  projection_start: string
  dates: string[]
  groups: ProjectionGroup[]
  /** 日別出荷予定（確定受注優先、無ければ内示） */
  demand_daily: Record<string, number>
  product_count: number
  month_workdays?: number
  production_qty_rule?: string
  /** 実績を採用する上限日（当日）。これより後の日付は実績 0 として扱う */
  actual_until?: string
  /** 工程 key → 実績最終日（この日以前は実績、以降は計画を採用） */
  actual_cutoff?: Record<string, string>
  /** 製品ルート分岐の件数（成型/社内メッキの次工程） */
  route_branch_stats?: {
    molding_next: Record<string, number>
    plating_next: Record<string, number>
  }
}

export interface ProjectionDetailRow {
  product_cd: string
  product_name: string
  by_date: Record<string, number>
  month_end: number
  route_sequence?: string[]
  molding_next?: string | null
  plating_next?: string | null
}

export interface ProjectionDetailData {
  year_month: string
  base_date: string
  projection_start: string
  dates: string[]
  process_key: string
  rows: ProjectionDetailRow[]
}

export function fetchProjectionSummary(params: {
  year_month: string
  base_date?: string
  force?: boolean
}): Promise<{ success: boolean; data: ProjectionSummaryData }> {
  return request.get(`${BASE}/summary`, {
    params: {
      year_month: params.year_month,
      base_date: params.base_date || undefined,
      force: params.force || undefined,
    },
  }) as unknown as Promise<{ success: boolean; data: ProjectionSummaryData }>
}

export function fetchProjectionDetail(params: {
  year_month: string
  process_key: string
  base_date?: string
}): Promise<{ success: boolean; data: ProjectionDetailData }> {
  return request.get(`${BASE}/detail`, {
    params: {
      year_month: params.year_month,
      process_key: params.process_key,
      base_date: params.base_date || undefined,
    },
  }) as unknown as Promise<{ success: boolean; data: ProjectionDetailData }>
}

/** 計画合計の手動修正（日別×工程） */
export interface PlanOverrideItem {
  plan_date: string
  process_key: string
  /** null で削除 */
  qty: number | null
}

export interface PlanOverridesData {
  items: Array<{ plan_date: string; process_key: string; qty: number }>
  editable_process_keys: string[]
}

export function fetchPlanOverrides(params: {
  year_month: string
}): Promise<{ success: boolean; data: PlanOverridesData }> {
  return request.get(`${BASE}/plan-overrides`, {
    params: { year_month: params.year_month },
  }) as unknown as Promise<{ success: boolean; data: PlanOverridesData }>
}

export function savePlanOverrides(
  items: PlanOverrideItem[]
): Promise<{ success: boolean; data: { count: number } }> {
  return request.put(`${BASE}/plan-overrides`, { items }) as unknown as Promise<{
    success: boolean
    data: { count: number }
  }>
}

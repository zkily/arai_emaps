/**
 * 生産計画ベースライン API（月次ベースライン生成・比較・修正）
 */
import request from '@/shared/api/request'

export interface PlanBaselineComparisonItem {
  plan_date?: string
  process_name?: string
  baseline_plan?: number
  current_plan?: number
  plan_diff?: number
  current_actual?: number | null
  actual_diff?: number | null
  [key: string]: unknown
}

export interface PlanBaselineComparisonSummary {
  baselinePlanTotal?: number | null
  currentPlanTotal?: number | null
  planDifference?: number | null
  currentActualTotal?: number | null
  actualDifference?: number | null
  planAchievementRatio?: number | null
  [key: string]: unknown
}

export interface PlanBaselineComparisonResult {
  success?: boolean
  baselineMonth?: string
  summary?: PlanBaselineComparisonSummary
  items?: PlanBaselineComparisonItem[]
}

export interface PlanBaselineRecord {
  plan_date: string
  process_name: string
  plan_quantity: number
  actual_quantity?: number
  machine_name?: string
  product_cd?: string
  product_name?: string
}

/** 比較データ取得 */
export async function fetchPlanBaselineComparison(params: {
  baselineMonth: string
  processName?: string
}): Promise<PlanBaselineComparisonResult | null> {
  const res = await request.get<PlanBaselineComparisonResult>('/api/plan-baseline/comparison', {
    params: { baselineMonth: params.baselineMonth, processName: params.processName },
  })
  if (res && (res as PlanBaselineComparisonResult).summary !== undefined) {
    return res as PlanBaselineComparisonResult
  }
  if (res && (res as PlanBaselineComparisonResult).items) {
    return res as PlanBaselineComparisonResult
  }
  return null
}

/** ベースライン生成 */
export async function generatePlanBaseline(params: {
  baselineMonth: string
  processName?: string
}): Promise<void> {
  await request.post('/api/plan-baseline/generate', {
    baselineMonth: params.baselineMonth,
    processName: params.processName,
  })
}

/** ベースライン削除 */
export async function deletePlanBaseline(params: {
  baselineMonth: string
  processName?: string
}): Promise<void> {
  await request.delete('/api/plan-baseline/delete', {
    params: { baselineMonth: params.baselineMonth, processName: params.processName },
  })
}

/** 修正用レコード一覧 */
export async function fetchPlanBaselineRecords(params: {
  baselineMonth: string
  processName?: string
}): Promise<PlanBaselineRecord[]> {
  const res = await request.get<PlanBaselineRecord[]>('/api/plan-baseline/records', {
    params: { baselineMonth: params.baselineMonth, processName: params.processName },
  })
  if (Array.isArray(res)) return res
  return []
}

/** 計画数量の更新（1件） */
export async function updatePlanBaselinePlanQuantity(params: {
  baselineMonth: string
  planDate: string
  processName?: string
  planQuantity: number
}): Promise<void> {
  await request.put('/api/plan-baseline/plan-quantity', {
    baselineMonth: params.baselineMonth,
    planDate: params.planDate,
    processName: params.processName,
    planQuantity: params.planQuantity,
  })
}

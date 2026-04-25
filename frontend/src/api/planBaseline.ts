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

/** production_plan_rate（操業度）一覧用 */
export interface PlanOperationRateRow {
  id?: number
  file_name?: string
  processed_at?: string | null
  machine_cd?: string | null
  machine_name?: string | null
  operation_variance?: string
  display_process?: string
  display_month?: string
}

interface PlanOperationRateResponse {
  success?: boolean
  message?: string
  items?: PlanOperationRateRow[]
  count?: number
}

/** 操業度（production_plan_rate）取得。月・工程（成型/溶接）で絞り込み可 */
export async function fetchPlanOperationRate(params: {
  monthNum?: number
  processName?: string
}): Promise<PlanOperationRateRow[]> {
  const qp: Record<string, number | string> = {}
  if (params.monthNum != null && params.monthNum >= 1 && params.monthNum <= 12) {
    qp.monthNum = params.monthNum
  }
  const p = params.processName?.trim()
  if (p) qp.processName = p
  const res = (await request.get<PlanOperationRateResponse>(
    '/api/plan-baseline/plan-operation-rate',
    {
      params: qp,
    },
  )) as PlanOperationRateResponse
  if (res?.success === false) {
    throw new Error(res.message || '操業度データの取得に失敗しました')
  }
  return Array.isArray(res?.items) ? res.items : []
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

/** ベースライン生成（メッキ・検査は weekdayBaseline 必須・土日任意） */
export async function generatePlanBaseline(params: {
  baselineMonth: string
  processName?: string
  /** メッキ・検査：平日（月〜金）各日の基準計画 */
  weekdayBaseline?: number
  /** 土曜に行を作る場合の数量（未指定時は土曜は作らない） */
  saturdayBaseline?: number
  /** 日曜に行を作る場合の数量（未指定時は日曜は作らない） */
  sundayBaseline?: number
}): Promise<void> {
  const body: Record<string, unknown> = {
    baselineMonth: params.baselineMonth,
    processName: params.processName,
  }
  if (params.weekdayBaseline != null && !Number.isNaN(params.weekdayBaseline)) {
    body.weekdayBaseline = params.weekdayBaseline
  }
  if (params.saturdayBaseline != null && !Number.isNaN(params.saturdayBaseline)) {
    body.saturdayBaseline = params.saturdayBaseline
  }
  if (params.sundayBaseline != null && !Number.isNaN(params.sundayBaseline)) {
    body.sundayBaseline = params.sundayBaseline
  }
  await request.post('/api/plan-baseline/generate', body)
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

/** ベースライン 1 件削除（修正ダイアログ用） */
export async function deletePlanBaselineRecord(params: {
  baselineMonth: string
  planDate: string
  processName?: string
}): Promise<void> {
  const res = (await request.delete<{ success?: boolean; message?: string }>(
    '/api/plan-baseline/record',
    {
      params: {
        baselineMonth: params.baselineMonth,
        planDate: params.planDate,
        processName: params.processName ?? '',
      },
    },
  )) as unknown as { success?: boolean; message?: string }
  if (res && typeof res === 'object' && res.success === false) {
    throw new Error(res.message || '削除に失敗しました')
  }
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

/** 工程別PDFを指定フォルダに保存（FormData: baselineMonth + files） */
export async function exportPlanBaselinePdfToFolder(
  baselineMonth: string,
  files: { processName: string; blob: Blob }[],
): Promise<{ success: boolean; message?: string; saved?: string[]; errors?: string[] }> {
  const form = new FormData()
  form.append('baselineMonth', baselineMonth)
  files.forEach(({ processName, blob }) => {
    form.append('files', blob, `${processName}.pdf`)
  })
  const res = (await request.post<{
    success: boolean
    message?: string
    saved?: string[]
    errors?: string[]
  }>('/api/plan-baseline/export-pdf-to-folder', form)) as unknown as {
    success: boolean
    message?: string
    saved?: string[]
    errors?: string[]
  }
  return res ?? { success: false, message: 'レスポンスがありません' }
}

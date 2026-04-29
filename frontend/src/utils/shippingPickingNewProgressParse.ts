/**
 * 出荷ピッキング new-progress API のレスポンス正規化・フィルタ
 * （ShippingPickingHome の fetchProgressData と同一ロジックを共有）
 */
import { getJSTToday } from '@/utils/dateFormat'

export interface ShippingPickingTodayOverview {
  total_today: number
  pending_today: number
  completed_today: number
  today_completion_rate: number
}

export type NormalizedPickingProgressResult =
  | { ok: false; message?: string }
  | { ok: true; responseData: Record<string, unknown> }

/** request インターセプタ後の生レスポンスを data オブジェクトに正規化 */
export function normalizePickingProgressResponse(response: unknown): NormalizedPickingProgressResult {
  if (Array.isArray(response)) {
    return {
      ok: true,
      responseData: { palletList: response, progressStats: [], todayOverview: {} },
    }
  }
  if (response && typeof response === 'object') {
    const obj = response as Record<string, unknown>
    if (obj.success !== undefined) {
      if (!obj.success) {
        return { ok: false, message: typeof obj.message === 'string' ? obj.message : undefined }
      }
      const d = obj.data
      return {
        ok: true,
        responseData:
          d && typeof d === 'object' && !Array.isArray(d) ? (d as Record<string, unknown>) : {},
      }
    }
    return { ok: true, responseData: obj }
  }
  return { ok: false }
}

/**
 * 製品名フィルタ後、palletList から本日分を再集計して todayOverview を更新
 */
export function filterProductDataForPickingProgress(data: unknown): Record<string, unknown> | unknown[] {
  if (!data) return data as Record<string, unknown>

  const excludeKeywords = ['加工', 'アーチ', '料金']
  const shouldExclude = (productName: string) =>
    Boolean(productName) && excludeKeywords.some((keyword) => productName.includes(keyword))

  if (Array.isArray(data)) {
    return data.filter((item: Record<string, unknown>) => {
      const productName = String(item.product_name || item.productName || '')
      return !shouldExclude(productName)
    })
  }

  if (typeof data === 'object') {
    const filtered = { ...(data as Record<string, unknown>) }

    if (Array.isArray(filtered.palletList)) {
      filtered.palletList = filtered.palletList.filter((item: Record<string, unknown>) => {
        const productName = String(item.product_name || item.productName || '')
        return !shouldExclude(productName)
      })
    }

    if (Array.isArray(filtered.progressStats)) {
      filtered.progressStats = filtered.progressStats.filter((item: Record<string, unknown>) => {
        const productName = String(item.product_name || item.productName || '')
        return !shouldExclude(productName)
      })
    }

    if (Array.isArray(filtered.palletList)) {
      const today = getJSTToday()
      const todayItems = filtered.palletList.filter((item: Record<string, unknown>) => {
        const itemDate = String(item.shipping_date || item.date || '')
        return itemDate === today || itemDate.startsWith(today)
      })

      if (todayItems.length > 0) {
        const pendingStatuses = ['pending', '進行中', 'in_progress']
        const completedStatuses = ['completed', '完了', 'finished']

        const totalToday = todayItems.length
        const pendingToday = todayItems.filter((item: Record<string, unknown>) =>
          pendingStatuses.includes(String(item.status)),
        ).length
        const completedToday = todayItems.filter((item: Record<string, unknown>) =>
          completedStatuses.includes(String(item.status)),
        ).length
        const completionRate = totalToday > 0 ? Math.round((completedToday / totalToday) * 100) : 0

        filtered.todayOverview = {
          total_today: totalToday,
          pending_today: pendingToday,
          completed_today: completedToday,
          today_completion_rate: completionRate,
        }
        filtered.palletList = todayItems
      } else {
        const overview = (filtered.todayOverview || {}) as Record<string, number>
        filtered.todayOverview = {
          total_today: overview.total_today || 0,
          pending_today: overview.pending_today || 0,
          completed_today: overview.completed_today || 0,
          today_completion_rate: overview.today_completion_rate || 0,
        }
      }
    }

    return filtered
  }

  return data as Record<string, unknown>
}

export function parseTodayOverviewFromPickingProgressResponse(
  rawResponse: unknown,
): ShippingPickingTodayOverview | null {
  const normalized = normalizePickingProgressResponse(rawResponse)
  if (!normalized.ok) return null
  const filtered = filterProductDataForPickingProgress(normalized.responseData)
  if (!filtered || typeof filtered !== 'object' || Array.isArray(filtered)) return null
  const overview = (filtered as Record<string, unknown>).todayOverview as
    | ShippingPickingTodayOverview
    | undefined
    | null
  if (!overview || typeof overview !== 'object') return null
  return {
    total_today: Number(overview.total_today) || 0,
    pending_today: Number(overview.pending_today) || 0,
    completed_today: Number(overview.completed_today) || 0,
    today_completion_rate: Number(overview.today_completion_rate) || 0,
  }
}

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

const PICKING_EXCLUDE_NAME_KEYWORDS = ['加工', 'アーチ', '料金'] as const

/** 空・未設定は量産品扱い。試作品・代替品等はピッキング管理から除外 */
export function isPickingMassProductionType(productType: unknown): boolean {
  const t = String(productType ?? '').trim()
  return t === '' || t === '量産品'
}

/** 製品名キーワード・製品タイプがピッキング管理の表示・集計対象か */
export function shouldIncludeInPickingDisplay(item: {
  product_name?: unknown
  productName?: unknown
  product_type?: unknown
  productType?: unknown
}): boolean {
  const productName = String(item.product_name || item.productName || '')
  if (productName && PICKING_EXCLUDE_NAME_KEYWORDS.some((keyword) => productName.includes(keyword))) {
    return false
  }
  return isPickingMassProductionType(item.product_type ?? item.productType)
}

/** 品番行のピッキング完了判定（フラグまたは status） */
export function isPickingItemCompleted(item: {
  status?: unknown
  picking_log_matched?: unknown
}): boolean {
  const st = String(item.status || '')
  return st === 'completed' || st === 'picked' || Number(item.picking_log_matched || 0) === 1
}

/** パレット番号。shipping_no_p は品番付きのピッキング単位なので使わない */
export function pickingPalletKey(item: { shipping_no?: unknown; shipping_no_p?: unknown }): string {
  const no = String(item.shipping_no || '').trim()
  return no || String(item.shipping_no_p || '').trim()
}

export type PickingPalletStatus = 'completed' | 'picking' | 'pending'

/** 同一パレット内の品番行からパレット状態を算出。一部完了は作業中（未ピッキングにしない） */
export function summarizePickingPalletStatus(
  items: Array<{ status?: unknown; picking_log_matched?: unknown }>,
): PickingPalletStatus {
  if (!items.length) return 'pending'
  const completedCount = items.filter((item) => isPickingItemCompleted(item)).length
  if (completedCount === items.length) return 'completed'
  if (completedCount > 0 || items.some((item) => String(item.status || '') === 'picking')) {
    return 'picking'
  }
  return 'pending'
}

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
 * 製品名フィルタ・量産品以外除外後、palletList から本日分を再集計して todayOverview を更新
 */
export function filterProductDataForPickingProgress(data: unknown): Record<string, unknown> | unknown[] {
  if (!data) return data as Record<string, unknown>

  if (Array.isArray(data)) {
    return data.filter((item: Record<string, unknown>) => shouldIncludeInPickingDisplay(item))
  }

  if (typeof data === 'object') {
    const filtered = { ...(data as Record<string, unknown>) }

    if (Array.isArray(filtered.palletList)) {
      filtered.palletList = filtered.palletList.filter((item: Record<string, unknown>) =>
        shouldIncludeInPickingDisplay(item),
      )
    }

    if (Array.isArray(filtered.progressStats)) {
      filtered.progressStats = filtered.progressStats.filter((item: Record<string, unknown>) => {
        if (item.product_name || item.productName || item.product_type || item.productType) {
          return shouldIncludeInPickingDisplay(item)
        }
        return true
      })
    }

    if (Array.isArray(filtered.palletList)) {
      const today = getJSTToday()
      const todayItems = filtered.palletList.filter((item: Record<string, unknown>) => {
        const itemDate = String(item.shipping_date || item.date || '')
        return itemDate === today || itemDate.startsWith(today)
      })

      if (todayItems.length > 0) {
        const pallets = new Map<string, Record<string, unknown>[]>()
        todayItems.forEach((item: Record<string, unknown>) => {
          const key = pickingPalletKey(item)
          if (!key) return
          const list = pallets.get(key)
          if (list) list.push(item)
          else pallets.set(key, [item])
        })
        let completedToday = 0
        let unfinishedToday = 0
        pallets.forEach((items) => {
          if (summarizePickingPalletStatus(items) === 'completed') completedToday++
          else unfinishedToday++
        })
        const totalToday = pallets.size
        const completionRate = totalToday > 0 ? Math.round((completedToday / totalToday) * 100) : 0

        filtered.todayOverview = {
          total_today: totalToday,
          pending_today: unfinishedToday,
          completed_today: completedToday,
          today_completion_rate: completionRate,
        }
        filtered.palletList = todayItems
      } else {
        filtered.todayOverview = {
          total_today: 0,
          pending_today: 0,
          completed_today: 0,
          today_completion_rate: 0,
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

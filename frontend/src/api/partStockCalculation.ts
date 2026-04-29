import request from '@/shared/api/request'

const PREFIX = '/api/part/stock'

export async function getCurrentPartStockStatus(): Promise<{
  success?: boolean
  data?: unknown[]
}> {
  try {
    const res = await request.get(`${PREFIX}/latest`)
    const data = (res as any)?.data ?? res
    return { success: true, data: Array.isArray(data) ? data : (data?.list ?? []) }
  } catch (e) {
    console.warn('getCurrentPartStockStatus:', e)
    return { success: false, data: [] }
  }
}

export async function calculatePartStock(params?: {
  start_date?: string
  end_date?: string
}): Promise<{
  success?: boolean
  data?: {
    calculated_count: number
    updated_count: number
    usage_synced?: number
    usage_plan_synced?: number
    /** 受払×BOM 集計で得た (部品,日) キー数（0 ならログまたは BOM consume_process_cd を要確認） */
    usage_lookup_key_count?: number
    usage_map_nonzero?: number
    /** 同期期間内の part_stock 行数 */
    sync_window_row_count?: number
    usage_period?: {
      /** クリア・ローリングの実効同期期間（initial>0 最遅日～表内最大日） */
      start_date: string
      end_date: string
      calculation_start_date?: string
      usage_sync_from_request?: boolean
      /** 使用数・使用計画集計に使ったクエリ区間 */
      usage_map_query_start?: string
      usage_map_query_end?: string
    } | null
  }
}> {
  const res = await request.post(`${PREFIX}/calculate`, params ?? {})
  const raw = (res as any)?.data ?? res
  const success = raw?.success !== false
  const data = raw?.data ?? raw
  return {
    success,
    data: {
      calculated_count: data?.calculated_count ?? 0,
      updated_count: data?.updated_count ?? 0,
      usage_synced: data?.usage_synced ?? 0,
      usage_plan_synced: data?.usage_plan_synced ?? 0,
      usage_lookup_key_count: data?.usage_lookup_key_count ?? 0,
      usage_map_nonzero: data?.usage_map_nonzero ?? 0,
      sync_window_row_count: data?.sync_window_row_count ?? 0,
      usage_period: data?.usage_period ?? null,
    },
  }
}

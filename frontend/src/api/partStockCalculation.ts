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
    usage_period?: {
      start_date: string
      end_date: string
      calculation_start_date?: string
      usage_sync_from_request?: boolean
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
      usage_period: data?.usage_period ?? null,
    },
  }
}

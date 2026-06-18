import type { WarehouseNegativeTodayResponse } from '@/api/database'

export interface WarehouseNegativeHeaderOverview {
  as_of: string
  count: number
  samples: Array<{
    product_cd: string
    product_name: string
    warehouse_inventory: number
  }>
}

export function parseWarehouseNegativeOverview(raw: unknown): WarehouseNegativeHeaderOverview | null {
  const payload =
    (raw as { data?: WarehouseNegativeTodayResponse })?.data ??
    (raw as WarehouseNegativeTodayResponse | undefined)
  if (!payload || !payload.count || payload.count <= 0) return null

  return {
    as_of: payload.as_of,
    count: payload.count,
    samples: (payload.list || []).slice(0, 6).map((row) => ({
      product_cd: row.product_cd,
      product_name: row.product_name,
      warehouse_inventory: row.warehouse_inventory,
    })),
  }
}

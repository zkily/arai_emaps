import request from '@/shared/api/request'

const PREFIX = '/api/part/stock'

export interface PartQuantityUpdate {
  material_cd?: string
  part_cd?: string
  date: string
  initial_stock?: number
  adjustment_quantity?: number
  usage_quantity?: number
  order_quantity?: number
  order_bundle_quantity?: number
  order_amount?: number
  usage_plan_qty?: number
  stock_trend?: number
}

export interface PartRemarksUpdate {
  material_cd?: string
  part_cd?: string
  date: string
  remarks?: string
}

function resolvePartCd(p: PartQuantityUpdate | PartRemarksUpdate): string {
  return (p.part_cd || p.material_cd || '').trim()
}

export async function updatePartQuantities(params: PartQuantityUpdate): Promise<{ success?: boolean; message?: string }> {
  try {
    const part_cd = resolvePartCd(params)
    if (!part_cd) return { success: false, message: 'part_cd がありません' }
    const listRes = await request.get<{ success?: boolean; data?: { list: { id: number }[] } }>(`${PREFIX}`, {
      params: { part_cd, target_date: params.date, pageSize: 1 },
    })
    const list = (listRes as any)?.data?.list ?? (listRes as any)?.list
    const id = Array.isArray(list) && list[0] ? (list[0] as { id: number }).id : null
    if (id) {
      const body: Record<string, unknown> = {}
      if (params.initial_stock !== undefined) body.initial_stock = params.initial_stock
      if (params.adjustment_quantity !== undefined) body.adjustment_quantity = params.adjustment_quantity
      if (params.usage_quantity !== undefined) body.planned_usage = params.usage_quantity
      if (params.order_quantity !== undefined) body.order_quantity = params.order_quantity
      if (params.order_bundle_quantity !== undefined) body.order_bundle_quantity = params.order_bundle_quantity
      if (params.order_amount !== undefined) body.order_amount = params.order_amount
      if (params.usage_plan_qty !== undefined) body.usage_plan_qty = params.usage_plan_qty
      if (params.stock_trend !== undefined) body.stock_trend = params.stock_trend
      await request.put(`${PREFIX}/${id}`, body)
      return { success: true }
    }
    return { success: false, message: '該当レコードが見つかりません' }
  } catch (e) {
    console.warn('updatePartQuantities:', e)
    return { success: false, message: (e as Error).message }
  }
}

export async function updatePartRemarks(params: PartRemarksUpdate): Promise<{ success?: boolean; message?: string }> {
  try {
    const part_cd = resolvePartCd(params)
    if (!part_cd) return { success: false, message: 'part_cd がありません' }
    const listRes = await request.get<{ success?: boolean; data?: { list: { id: number }[] } }>(`${PREFIX}`, {
      params: { part_cd, target_date: params.date, pageSize: 1 },
    })
    const list = (listRes as any)?.data?.list ?? (listRes as any)?.list
    const id = Array.isArray(list) && list[0] ? (list[0] as { id: number }).id : null
    if (id) {
      await request.put(`${PREFIX}/${id}`, { remarks: params.remarks })
      return { success: true }
    }
    return { success: false, message: '該当レコードが見つかりません' }
  } catch (e) {
    console.warn('updatePartRemarks:', e)
    return { success: false, message: (e as Error).message }
  }
}

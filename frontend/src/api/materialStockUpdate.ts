/**
 * 材料在庫更新 API（/api/material/stock に対応）
 * 数量・備考の更新は backend の PUT /api/material/stock/{id} または stock/sub/{id} を使用
 */
import request from '@/shared/api/request'

const PREFIX = '/api/material/stock'

export interface MaterialQuantityUpdate {
  material_cd: string
  date: string
  initial_stock?: number
  adjustment_quantity?: number
  usage_quantity?: number
  order_quantity?: number
  order_bundle_quantity?: number
  bundle_weight?: number
  order_amount?: number
}

export interface MaterialRemarksUpdate {
  material_cd: string
  date: string
  remarks?: string
}

/** 指定されたフィールドのみ PUT ボディに含める（未指定フィールドで DB を上書きしない） */
function buildQuantityBody(params: MaterialQuantityUpdate): Record<string, number> {
  const body: Record<string, number> = {}
  if (params.initial_stock !== undefined) body.initial_stock = params.initial_stock
  if (params.adjustment_quantity !== undefined) {
    body.adjustment_quantity = params.adjustment_quantity
  }
  if (params.usage_quantity !== undefined) body.planned_usage = params.usage_quantity
  if (params.order_quantity !== undefined) body.order_quantity = params.order_quantity
  if (params.order_bundle_quantity !== undefined) {
    body.order_bundle_quantity = params.order_bundle_quantity
  }
  if (params.bundle_weight !== undefined) body.bundle_weight = params.bundle_weight
  if (params.order_amount !== undefined) body.order_amount = params.order_amount
  return body
}

/** 数量系フィールド更新（主表 or 子表の行 id がある場合は PUT で更新） */
export async function updateMaterialQuantities(
  params: MaterialQuantityUpdate
): Promise<{ success?: boolean; message?: string }> {
  try {
    const listRes = await request.get<{ success?: boolean; data?: { list: { id: number }[] } }>(
      `${PREFIX}`,
      {
        params: { material_cd: params.material_cd, target_date: params.date, pageSize: 1 },
      }
    )
    const list = (listRes as any)?.data?.list ?? (listRes as any)?.list
    const id = Array.isArray(list) && list[0] ? (list[0] as { id: number }).id : null
    if (id) {
      await request.put(`${PREFIX}/${id}`, buildQuantityBody(params))
      return { success: true }
    }
    return { success: false, message: '該当レコードが見つかりません' }
  } catch (e) {
    console.warn('updateMaterialQuantities:', e)
    return { success: false, message: (e as Error).message }
  }
}

/** 備考更新 */
export async function updateMaterialRemarks(
  params: MaterialRemarksUpdate
): Promise<{ success?: boolean; message?: string }> {
  try {
    const listRes = await request.get<{ success?: boolean; data?: { list: { id: number }[] } }>(
      `${PREFIX}`,
      {
        params: { material_cd: params.material_cd, target_date: params.date, pageSize: 1 },
      }
    )
    const list = (listRes as any)?.data?.list ?? (listRes as any)?.list
    const id = Array.isArray(list) && list[0] ? (list[0] as { id: number }).id : null
    if (id) {
      await request.put(`${PREFIX}/${id}`, { remarks: params.remarks })
      return { success: true }
    }
    return { success: false, message: '該当レコードが見つかりません' }
  } catch (e) {
    console.warn('updateMaterialRemarks:', e)
    return { success: false, message: (e as Error).message }
  }
}

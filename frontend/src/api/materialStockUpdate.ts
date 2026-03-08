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
      await request.put(`${PREFIX}/${id}`, {
        initial_stock: params.initial_stock,
        adjustment_quantity: params.adjustment_quantity,
        planned_usage: params.usage_quantity,
        order_quantity: params.order_quantity,
        order_bundle_quantity: params.order_bundle_quantity,
        bundle_weight: params.bundle_weight,
        order_amount: params.order_amount,
      })
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

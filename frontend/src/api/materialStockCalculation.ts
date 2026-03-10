/**
 * 材料在庫計算
 * - getCurrentMaterialStockStatus: 現在の在庫状態取得
 * - calculateMaterialStock: 在庫再計算（initial_stock>0 の最終日から current_stock を算出し DB 更新）
 */
import request from '@/shared/api/request'

const PREFIX = '/api/material/stock'

/** 現在の材料在庫状態を取得（latest または list から算出） */
export async function getCurrentMaterialStockStatus(): Promise<{
  success?: boolean
  data?: unknown[]
}> {
  try {
    const res = await request.get(`${PREFIX}/latest`)
    const data = (res as any)?.data ?? (res as any)
    return { success: true, data: Array.isArray(data) ? data : (data?.list ?? []) }
  } catch (e) {
    console.warn('getCurrentMaterialStockStatus:', e)
    return { success: false, data: [] }
  }
}

export interface CalculateMaterialStockResult {
  success?: boolean
  data?: {
    calculated_count: number
    updated_count: number
  }
}

/** 材料在庫計算: 各材料で initial_stock>0 の最終日から current_stock を再計算し DB を更新 */
export async function calculateMaterialStock(): Promise<CalculateMaterialStockResult> {
  try {
    const res = await request.post(`${PREFIX}/calculate`)
    const raw = (res as any)?.data ?? res
    const success = raw?.success !== false
    const data = raw?.data ?? raw
    return {
      success,
      data: {
        calculated_count: data?.calculated_count ?? 0,
        updated_count: data?.updated_count ?? 0,
      },
    }
  } catch (e) {
    console.warn('calculateMaterialStock:', e)
    return { success: false, data: { calculated_count: 0, updated_count: 0 } }
  }
}

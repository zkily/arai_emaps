/**
 * 材料在庫データ生成（backend の /api/material/stock 登録に対応するスタブ）
 */
import request from '@/shared/api/request'

const PREFIX = '/api/material/stock'

export interface GenerateMaterialStockParams {
  material_cd?: string
  material_name?: string
  date?: string
  [key: string]: unknown
}

/** 材料在庫データを生成・登録（POST /api/material/stock） */
export async function generateMaterialStockData(
  params: GenerateMaterialStockParams
): Promise<{ success?: boolean; data?: unknown; message?: string }> {
  try {
    const res = await request.post(PREFIX, params)
    const data = (res as any)?.data ?? res
    return { success: true, data }
  } catch (e) {
    console.warn('generateMaterialStockData:', e)
    return { success: false, message: (e as Error).message }
  }
}

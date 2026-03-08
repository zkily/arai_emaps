/**
 * 材料在庫計算（現状は backend の /api/material/stock を利用したスタブ）
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

/** 材料在庫計算（一覧取得のラッパー） */
export async function calculateMaterialStock(): Promise<{ success?: boolean; data?: unknown[] }> {
  try {
    const res = await request.get(`${PREFIX}`, { params: { page: 1, pageSize: 10000 } })
    const raw = (res as any)?.data ?? res
    const list = raw?.list ?? (Array.isArray(raw) ? raw : [])
    return { success: true, data: list }
  } catch (e) {
    console.warn('calculateMaterialStock:', e)
    return { success: false, data: [] }
  }
}

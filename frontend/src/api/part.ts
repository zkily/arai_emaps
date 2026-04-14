/**
 * 部品購買・在庫 API（/api/part/*）
 */
import request from '@/shared/api/request'

const PREFIX = '/api/part'

export function getPartStockSupplierNames(): Promise<{ success?: boolean; data?: string[] }> {
  return request.get(`${PREFIX}/stock/supplier-names`)
}

export function getPartStockList(params?: {
  page?: number
  pageSize?: number
  keyword?: string
  part_cd?: string
  material_cd?: string
  supplier_cd?: string
  suppliers?: string
  target_date?: string
  start_date?: string
  end_date?: string
  order_only?: boolean
}): Promise<{ success?: boolean; data?: { list: unknown[]; total: number } }> {
  const p = { ...params }
  if (p.material_cd && !p.part_cd) p.part_cd = p.material_cd
  return request.get(`${PREFIX}/stock`, { params: p })
}

export function updatePartStock(
  id: number,
  body: Record<string, unknown>,
): Promise<{ success?: boolean; data?: unknown }> {
  return request.put(`${PREFIX}/stock/${id}`, body)
}

/** 部品在庫メイン行の新規登録（手入力注文など） */
export function createPartStock(
  body: Record<string, unknown>,
): Promise<{ success?: boolean; data?: unknown }> {
  return request.post(`${PREFIX}/stock`, body)
}

export function syncPartStockFromMaster(params?: {
  start_date?: string
  end_date?: string
}): Promise<{ success?: boolean; data?: { updated_count: number } }> {
  return request.post(`${PREFIX}/stock/sync-part-master`, params ?? {})
}

export function saveMaruichiPartOrderPdf(
  blob: Blob,
  filename: string,
): Promise<{ success?: boolean; message?: string; path?: string; detail?: string }> {
  const form = new FormData()
  form.append('file', blob, filename)
  return request.post(`${PREFIX}/stock/maruichi-order-pdf`, form, { timeout: 120000 })
}

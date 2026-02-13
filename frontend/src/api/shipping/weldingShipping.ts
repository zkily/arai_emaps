/**
 * 溶接出荷管理 API（スライディング溶接出荷）
 */
import request from '@/utils/request'

export interface WeldingProduct {
  value: string
  label: string
}

export interface WeldingShippingRecord {
  boxes: number
}

export interface WeldingShippingData {
  dates: string[]
  destinations: string[]
  products: Array<{ cd: string; name: string }>
  data: Record<string, Record<string, Record<string, WeldingShippingRecord[]>>>
}

export interface WeldingShippingDataParams {
  start_date: string
  end_date: string
  products: string[]
}

export interface WeldingExportParams {
  start_date: string
  end_date: string
  products: string[]
  table_data: WeldingShippingData
}

/** 溶接製品一覧を取得 */
export function getWeldingProducts(): Promise<WeldingProduct[]> {
  return request.get('/api/shipping/welding/products').then((r: unknown) => {
    if (Array.isArray(r)) return r as WeldingProduct[]
    const o = r as { data?: unknown }
    return (Array.isArray(o?.data) ? o.data : []) as WeldingProduct[]
  })
}

/** 溶接出荷データを取得。后端返回 { dates, destinations, products, data }，直接作为整体使用 */
export function getWeldingShippingData(params: WeldingShippingDataParams): Promise<WeldingShippingData> {
  return request.post('/api/shipping/welding/data', params).then((r: unknown) => {
    const body = r as WeldingShippingData
    if (body && typeof body === 'object' && Array.isArray(body.dates) && Array.isArray(body.products)) {
      return body
    }
    return r as WeldingShippingData
  })
}

/** 印刷用レポート HTML を取得 */
export function exportWeldingShippingReport(params: WeldingExportParams): Promise<{ html: string }> {
  return request.post('/api/shipping/welding/export', params).then((r: unknown) => {
    const o = r as { data?: { html?: string }; html?: string }
    if (o?.data?.html) return { html: o.data.html }
    if (typeof (o as { html?: string }).html === 'string') return { html: (o as { html: string }).html }
    return { html: '' }
  })
}

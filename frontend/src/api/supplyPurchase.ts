/**
 * 備品購入 API（仕入先別カタログ + 発注）
 */
import request from '@/shared/api/request'

export interface SupplyItem {
  id: number
  item_cd: string
  item_name: string
  specification: string
  unit: string
  pack_qty: number
  order_lot: number
  unit_price: number
  supplier_cd: string
  supplier_name?: string
  is_discontinued: boolean
  remarks: string
  created_at?: string | null
  updated_at?: string | null
}

export interface SupplyOrderLine {
  id?: number
  line_no: number
  item_cd: string
  item_name: string
  specification: string
  unit: string
  pack_qty: number
  order_lot: number
  order_qty: number
  unit_price: number
  amount: number
}

export interface SupplyPurchaseOrder {
  id: number
  order_no: string
  order_date: string | null
  delivery_date: string | null
  supplier_cd: string
  supplier_name: string
  status: string
  total_amount: number
  remarks: string
  created_by: string
  created_at?: string | null
  lines?: SupplyOrderLine[]
}

export interface SupplyItemPayload {
  item_cd: string
  item_name: string
  specification?: string
  unit?: string
  pack_qty: number
  order_lot: number
  unit_price: number
  supplier_cd: string
  is_discontinued?: boolean
  remarks?: string
}

type ListEnvelope<T> = { success?: boolean; data?: { list: T[]; total: number } }

const PREFIX = '/api/supply-purchase'

export async function fetchSupplyItems(params: {
  supplierCd?: string
  keyword?: string
  includeDiscontinued?: boolean
  discontinuedStatus?: '0' | '1'
  page?: number
  pageSize?: number
}): Promise<{ list: SupplyItem[]; total: number }> {
  const res = (await request.get(`${PREFIX}/items`, { params })) as ListEnvelope<SupplyItem>
  return { list: res.data?.list ?? [], total: res.data?.total ?? 0 }
}

export async function fetchNextSupplyItemCd(): Promise<string> {
  const res = (await request.get(`${PREFIX}/items/next-cd`)) as {
    data?: { item_cd?: string }
  }
  return res.data?.item_cd || 'B0001'
}

export async function createSupplyItem(body: SupplyItemPayload): Promise<SupplyItem> {
  const res = (await request.post(`${PREFIX}/items`, body)) as { data: SupplyItem }
  return res.data
}

export async function updateSupplyItem(
  id: number,
  body: Partial<SupplyItemPayload>,
): Promise<SupplyItem> {
  const res = (await request.put(`${PREFIX}/items/${id}`, body)) as { data: SupplyItem }
  return res.data
}

export async function deleteSupplyItem(id: number): Promise<void> {
  await request.delete(`${PREFIX}/items/${id}`)
}

export async function fetchSupplyOrders(params: {
  supplierCd?: string
  keyword?: string
  page?: number
  pageSize?: number
}): Promise<{ list: SupplyPurchaseOrder[]; total: number }> {
  const res = (await request.get(`${PREFIX}/orders`, {
    params,
  })) as ListEnvelope<SupplyPurchaseOrder>
  return { list: res.data?.list ?? [], total: res.data?.total ?? 0 }
}

export async function fetchSupplyOrder(id: number): Promise<SupplyPurchaseOrder> {
  const res = (await request.get(`${PREFIX}/orders/${id}`)) as { data: SupplyPurchaseOrder }
  return res.data
}

export async function createSupplyOrder(body: {
  supplier_cd: string
  order_date: string
  delivery_date?: string
  remarks?: string
  lines: { item_id: number; order_qty: number }[]
}): Promise<SupplyPurchaseOrder> {
  const res = (await request.post(`${PREFIX}/orders`, body)) as { data: SupplyPurchaseOrder }
  return res.data
}

export async function cancelSupplyOrder(id: number): Promise<void> {
  await request.post(`${PREFIX}/orders/${id}/cancel`)
}

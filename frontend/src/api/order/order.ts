/**
 * 日別受注（月订单维度）API - 日別管理弹窗用
 */
import {
  fetchOrderDailyList,
  updateOrderDaily,
  type OrderDailyItem,
} from '@/api/erp/orderDaily'
import request from '@/utils/request'

export type { OrderDailyItem }

/** 按月订单ID取得日別受注一覧（弹窗用格式） */
export async function fetchDailyOrdersByMonthlyOrderId(
  monthlyOrderId: string
): Promise<{ list: OrderDailyItem[] }> {
  const list = await fetchOrderDailyList({ monthly_order_id: monthlyOrderId })
  return { list: list ?? [] }
}

export interface BatchUpdateDailyItem {
  id: number
  forecast_units?: number
  confirmed_boxes?: number
  confirmed_units?: number
  status?: string
  remarks?: string
}

export interface BatchUpdateDailyResponse {
  success?: boolean
  updated?: number
}

/** 日別受注一括更新（1リクエストで一括送信、内示本数更新の高速化） */
export async function batchUpdateDailyOrders(params: {
  list: BatchUpdateDailyItem[]
}): Promise<BatchUpdateDailyResponse> {
  if (!params.list.length) return { success: true, updated: 0 }
  const res = await request.post('/api/erp/orders/daily/batch-update', {
    list: params.list,
  }) as BatchUpdateDailyResponse
  return res ?? { success: true, updated: params.list.length }
}

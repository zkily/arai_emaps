/**
 * 采购管理API
 */
import request from '@/utils/request'
import type {
  PurchaseOrder,
  PurchaseOrderItem,
  PurchaseReceipt,
  PurchaseReturn,
  PurchaseQueryParams,
  PurchaseStats
} from '@/types/erp/purchase'

const BASE_URL = '/api/erp/purchase'

// ========== 采购订单 ==========

/** 获取采购订单列表 */
export const getPurchaseOrderList = (params?: PurchaseQueryParams) => {
  return request.get<{ items: PurchaseOrder[]; total: number }>(`${BASE_URL}/orders`, { params })
}

/** 获取采购订单详情 */
export const getPurchaseOrderById = (id: number) => {
  return request.get<PurchaseOrder>(`${BASE_URL}/orders/${id}`)
}

/** 创建采购订单 */
export const createPurchaseOrder = (data: Partial<PurchaseOrder>) => {
  return request.post<PurchaseOrder>(`${BASE_URL}/orders`, data)
}

/** 更新采购订单 */
export const updatePurchaseOrder = (id: number, data: Partial<PurchaseOrder>) => {
  return request.put<PurchaseOrder>(`${BASE_URL}/orders/${id}`, data)
}

/** 删除采购订单 */
export const deletePurchaseOrder = (id: number) => {
  return request.delete(`${BASE_URL}/orders/${id}`)
}

/** 提交采购订单审批 */
export const submitPurchaseOrderForApproval = (id: number) => {
  return request.post(`${BASE_URL}/orders/${id}/submit`)
}

/** 审批采购订单 */
export const approvePurchaseOrder = (id: number, approved: boolean, remarks?: string) => {
  return request.post(`${BASE_URL}/orders/${id}/approve`, { approved, remarks })
}

/** 取消采购订单 */
export const cancelPurchaseOrder = (id: number, reason: string) => {
  return request.post(`${BASE_URL}/orders/${id}/cancel`, { reason })
}

// ========== 采购收货 ==========

/** 获取采购收货列表 */
export const getPurchaseReceiptList = (params?: {
  order_id?: number
  supplier_code?: string
  status?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}) => {
  return request.get<{ items: PurchaseReceipt[]; total: number }>(`${BASE_URL}/receipts`, { params })
}

/** 创建采购收货单 */
export const createPurchaseReceipt = (data: {
  order_id: number
  items: Array<{
    order_item_id: number
    received_quantity: number
    warehouse_code: string
    remarks?: string
  }>
  receipt_date?: string
  remarks?: string
}) => {
  return request.post<PurchaseReceipt>(`${BASE_URL}/receipts`, data)
}

/** 确认采购收货 */
export const confirmPurchaseReceipt = (id: number) => {
  return request.post(`${BASE_URL}/receipts/${id}/confirm`)
}

// ========== 采购退货 ==========

/** 获取采购退货列表 */
export const getPurchaseReturnList = (params?: {
  order_id?: number
  supplier_code?: string
  status?: string
  page?: number
  page_size?: number
}) => {
  return request.get<{ items: PurchaseReturn[]; total: number }>(`${BASE_URL}/returns`, { params })
}

/** 创建采购退货单 */
export const createPurchaseReturn = (data: Partial<PurchaseReturn>) => {
  return request.post<PurchaseReturn>(`${BASE_URL}/returns`, data)
}

/** 审批采购退货 */
export const approvePurchaseReturn = (id: number, approved: boolean, remarks?: string) => {
  return request.post(`${BASE_URL}/returns/${id}/approve`, { approved, remarks })
}

// ========== 采购统计 ==========

/** 获取采购统计数据 */
export const getPurchaseStats = (params?: {
  start_date?: string
  end_date?: string
}) => {
  return request.get<PurchaseStats>(`${BASE_URL}/stats`, { params })
}

/** 获取供应商采购排名 */
export const getSupplierPurchaseRanking = (params?: {
  start_date?: string
  end_date?: string
  limit?: number
}) => {
  return request.get<Array<{
    supplier_code: string
    supplier_name: string
    total_amount: number
    order_count: number
  }>>(`${BASE_URL}/stats/supplier-ranking`, { params })
}

/** 获取采购趋势 */
export const getPurchaseTrend = (params?: {
  start_date?: string
  end_date?: string
  group_by?: 'day' | 'week' | 'month'
}) => {
  return request.get<Array<{
    date: string
    total_amount: number
    order_count: number
  }>>(`${BASE_URL}/stats/trend`, { params })
}

/**
 * 销售管理API
 */
import request from '@/utils/request'
import type {
  SalesOrder,
  SalesOrderItem,
  SalesDelivery,
  SalesReturn,
  SalesQueryParams,
  SalesStats
} from '@/types/erp/sales'

const BASE_URL = '/api/erp/sales'

// ========== 销售订单 ==========

/** 获取销售订单列表 */
export const getSalesOrderList = (params?: SalesQueryParams) => {
  return request.get<{ items: SalesOrder[]; total: number }>(`${BASE_URL}/orders`, { params })
}

/** 获取销售订单详情 */
export const getSalesOrderById = (id: number) => {
  return request.get<SalesOrder>(`${BASE_URL}/orders/${id}`)
}

/** 创建销售订单 */
export const createSalesOrder = (data: Partial<SalesOrder>) => {
  return request.post<SalesOrder>(`${BASE_URL}/orders`, data)
}

/** 更新销售订单 */
export const updateSalesOrder = (id: number, data: Partial<SalesOrder>) => {
  return request.put<SalesOrder>(`${BASE_URL}/orders/${id}`, data)
}

/** 删除销售订单 */
export const deleteSalesOrder = (id: number) => {
  return request.delete(`${BASE_URL}/orders/${id}`)
}

/** 提交销售订单审批 */
export const submitSalesOrderForApproval = (id: number) => {
  return request.post(`${BASE_URL}/orders/${id}/submit`)
}

/** 审批销售订单 */
export const approveSalesOrder = (id: number, approved: boolean, remarks?: string) => {
  return request.post(`${BASE_URL}/orders/${id}/approve`, { approved, remarks })
}

/** 取消销售订单 */
export const cancelSalesOrder = (id: number, reason: string) => {
  return request.post(`${BASE_URL}/orders/${id}/cancel`, { reason })
}

// ========== 销售出库/发货 ==========

/** 获取销售发货列表 */
export const getSalesDeliveryList = (params?: {
  order_id?: number
  customer_code?: string
  status?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}) => {
  return request.get<{ items: SalesDelivery[]; total: number }>(`${BASE_URL}/deliveries`, { params })
}

/** 创建销售发货单 */
export const createSalesDelivery = (data: {
  order_id: number
  items: Array<{
    order_item_id: number
    delivery_quantity: number
    warehouse_code: string
    remarks?: string
  }>
  delivery_date?: string
  delivery_address?: string
  remarks?: string
}) => {
  return request.post<SalesDelivery>(`${BASE_URL}/deliveries`, data)
}

/** 确认发货 */
export const confirmSalesDelivery = (id: number, tracking_no?: string) => {
  return request.post(`${BASE_URL}/deliveries/${id}/confirm`, { tracking_no })
}

/** 完成发货 */
export const completeSalesDelivery = (id: number) => {
  return request.post(`${BASE_URL}/deliveries/${id}/complete`)
}

// ========== 销售退货 ==========

/** 获取销售退货列表 */
export const getSalesReturnList = (params?: {
  order_id?: number
  customer_code?: string
  status?: string
  page?: number
  page_size?: number
}) => {
  return request.get<{ items: SalesReturn[]; total: number }>(`${BASE_URL}/returns`, { params })
}

/** 创建销售退货单 */
export const createSalesReturn = (data: Partial<SalesReturn>) => {
  return request.post<SalesReturn>(`${BASE_URL}/returns`, data)
}

/** 审批销售退货 */
export const approveSalesReturn = (id: number, approved: boolean, remarks?: string) => {
  return request.post(`${BASE_URL}/returns/${id}/approve`, { approved, remarks })
}

/** 确认退货收货 */
export const confirmSalesReturnReceipt = (id: number, items: Array<{
  item_id: number
  received_quantity: number
  quality_status: string
  remarks?: string
}>) => {
  return request.post(`${BASE_URL}/returns/${id}/receive`, { items })
}

// ========== 销售统计 ==========

/** 获取销售统计数据 */
export const getSalesStats = (params?: {
  start_date?: string
  end_date?: string
}) => {
  return request.get<SalesStats>(`${BASE_URL}/stats`, { params })
}

/** 获取客户销售排名 */
export const getCustomerSalesRanking = (params?: {
  start_date?: string
  end_date?: string
  limit?: number
}) => {
  return request.get<Array<{
    customer_code: string
    customer_name: string
    total_amount: number
    order_count: number
  }>>(`${BASE_URL}/stats/customer-ranking`, { params })
}

/** 获取产品销售排名 */
export const getProductSalesRanking = (params?: {
  start_date?: string
  end_date?: string
  limit?: number
}) => {
  return request.get<Array<{
    product_code: string
    product_name: string
    total_quantity: number
    total_amount: number
  }>>(`${BASE_URL}/stats/product-ranking`, { params })
}

/** 获取销售趋势 */
export const getSalesTrend = (params?: {
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

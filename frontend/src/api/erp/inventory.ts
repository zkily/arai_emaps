/**
 * 库存管理API
 */
import request from '@/utils/request'
import type {
  Inventory,
  InventoryTransaction,
  InventoryAdjustment,
  StockAlert,
  InventoryQueryParams,
  InventoryStats
} from '@/types/erp/inventory'

const BASE_URL = '/api/erp/inventory'

// ========== 库存查询 ==========

/** 获取库存列表 */
export const getInventoryList = (params?: InventoryQueryParams) => {
  return request.get<{ items: Inventory[]; total: number }>(BASE_URL, { params })
}

/** 获取单个库存详情 */
export const getInventoryById = (id: number) => {
  return request.get<Inventory>(`${BASE_URL}/${id}`)
}

/** 按产品编码查询库存 */
export const getInventoryByProduct = (productCode: string) => {
  return request.get<Inventory[]>(`${BASE_URL}/product/${productCode}`)
}

/** 获取库存统计 */
export const getInventoryStats = () => {
  return request.get<InventoryStats>(`${BASE_URL}/stats`)
}

// ========== 库存操作 ==========

/** 创建库存记录 */
export const createInventory = (data: Partial<Inventory>) => {
  return request.post<Inventory>(BASE_URL, data)
}

/** 更新库存记录 */
export const updateInventory = (id: number, data: Partial<Inventory>) => {
  return request.put<Inventory>(`${BASE_URL}/${id}`, data)
}

/** 删除库存记录 */
export const deleteInventory = (id: number) => {
  return request.delete(`${BASE_URL}/${id}`)
}

// ========== 库存流水 ==========

/** 获取库存流水记录 */
export const getInventoryTransactions = (params?: {
  inventory_id?: number
  product_code?: string
  transaction_type?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}) => {
  return request.get<{ items: InventoryTransaction[]; total: number }>(
    `${BASE_URL}/transactions`,
    { params }
  )
}

/** 创建入库记录 */
export const createInboundTransaction = (data: {
  product_code: string
  warehouse_code: string
  quantity: number
  unit_cost?: number
  reference_no?: string
  remarks?: string
}) => {
  return request.post<InventoryTransaction>(`${BASE_URL}/inbound`, data)
}

/** 创建出库记录 */
export const createOutboundTransaction = (data: {
  product_code: string
  warehouse_code: string
  quantity: number
  reference_no?: string
  remarks?: string
}) => {
  return request.post<InventoryTransaction>(`${BASE_URL}/outbound`, data)
}

/** 库存调拨 */
export const createTransferTransaction = (data: {
  product_code: string
  from_warehouse_code: string
  to_warehouse_code: string
  quantity: number
  remarks?: string
}) => {
  return request.post<InventoryTransaction>(`${BASE_URL}/transfer`, data)
}

// ========== 库存调整 ==========

/** 获取库存调整记录 */
export const getInventoryAdjustments = (params?: {
  product_code?: string
  adjustment_type?: string
  status?: string
  page?: number
  page_size?: number
}) => {
  return request.get<{ items: InventoryAdjustment[]; total: number }>(
    `${BASE_URL}/adjustments`,
    { params }
  )
}

/** 创建库存调整申请 */
export const createInventoryAdjustment = (data: Partial<InventoryAdjustment>) => {
  return request.post<InventoryAdjustment>(`${BASE_URL}/adjustments`, data)
}

/** 审批库存调整 */
export const approveInventoryAdjustment = (id: number, approved: boolean, remarks?: string) => {
  return request.post(`${BASE_URL}/adjustments/${id}/approve`, { approved, remarks })
}

// ========== 库存预警 ==========

/** 获取库存预警列表 */
export const getStockAlerts = (params?: {
  alert_type?: string
  status?: string
  page?: number
  page_size?: number
}) => {
  return request.get<{ items: StockAlert[]; total: number }>(
    `${BASE_URL}/alerts`,
    { params }
  )
}

/** 处理库存预警 */
export const handleStockAlert = (id: number, action: string, remarks?: string) => {
  return request.post(`${BASE_URL}/alerts/${id}/handle`, { action, remarks })
}

// ========== 盘点 ==========

/** 创建盘点单 */
export const createStocktaking = (data: {
  warehouse_code: string
  product_codes?: string[]
  remarks?: string
}) => {
  return request.post(`${BASE_URL}/stocktaking`, data)
}

/** 提交盘点结果 */
export const submitStocktakingResult = (id: number, items: Array<{
  product_code: string
  actual_quantity: number
  remarks?: string
}>) => {
  return request.post(`${BASE_URL}/stocktaking/${id}/submit`, { items })
}

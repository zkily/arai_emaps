/**
 * 库存管理类型定义
 */

/** 库存记录 */
export interface Inventory {
  id: number
  product_code: string
  product_name: string
  warehouse_code: string
  warehouse_name: string
  quantity: number
  available_quantity: number
  reserved_quantity: number
  unit: string
  unit_cost: number
  total_cost: number
  location?: string
  batch_no?: string
  production_date?: string
  expiry_date?: string
  min_stock_level: number
  max_stock_level: number
  reorder_point: number
  is_active: boolean
  created_at: string
  updated_at: string
}

/** 库存流水记录 */
export interface InventoryTransaction {
  id: number
  transaction_no: string
  inventory_id: number
  product_code: string
  product_name: string
  warehouse_code: string
  warehouse_name: string
  transaction_type: 'inbound' | 'outbound' | 'transfer_in' | 'transfer_out' | 'adjustment'
  transaction_type_name: string
  quantity: number
  unit_cost: number
  total_cost: number
  balance_before: number
  balance_after: number
  reference_type?: string
  reference_no?: string
  reference_id?: number
  batch_no?: string
  remarks?: string
  created_by: string
  created_at: string
}

/** 库存调整记录 */
export interface InventoryAdjustment {
  id: number
  adjustment_no: string
  product_code: string
  product_name: string
  warehouse_code: string
  warehouse_name: string
  adjustment_type: 'increase' | 'decrease' | 'stocktaking'
  adjustment_type_name: string
  original_quantity: number
  adjustment_quantity: number
  new_quantity: number
  reason: string
  status: 'draft' | 'pending' | 'approved' | 'rejected'
  status_name: string
  remarks?: string
  created_by: string
  approved_by?: string
  approved_at?: string
  created_at: string
  updated_at: string
}

/** 库存预警 */
export interface StockAlert {
  id: number
  product_code: string
  product_name: string
  warehouse_code: string
  warehouse_name: string
  alert_type: 'low_stock' | 'overstock' | 'expiring' | 'expired'
  alert_type_name: string
  current_quantity: number
  threshold_quantity: number
  status: 'active' | 'acknowledged' | 'resolved'
  status_name: string
  remarks?: string
  created_at: string
  handled_at?: string
  handled_by?: string
}

/** 库存查询参数 */
export interface InventoryQueryParams {
  product_code?: string
  product_name?: string
  warehouse_code?: string
  category_code?: string
  has_stock?: boolean
  low_stock_only?: boolean
  page?: number
  page_size?: number
}

/** 库存统计 */
export interface InventoryStats {
  total_items: number
  total_value: number
  low_stock_count: number
  overstock_count: number
  expiring_soon_count: number
  warehouse_summary: Array<{
    warehouse_code: string
    warehouse_name: string
    item_count: number
    total_value: number
  }>
  category_summary: Array<{
    category_code: string
    category_name: string
    item_count: number
    total_value: number
  }>
}

/**
 * 销售管理类型定义
 */

/** 销售订单 */
export interface SalesOrder {
  id: number
  order_no: string
  customer_code: string
  customer_name: string
  order_date: string
  expected_delivery_date?: string
  delivery_address?: string
  status: 'draft' | 'pending' | 'approved' | 'partial_delivered' | 'completed' | 'cancelled'
  status_name: string
  currency: string
  exchange_rate: number
  subtotal: number
  tax_rate: number
  tax_amount: number
  discount_rate: number
  discount_amount: number
  total_amount: number
  received_amount: number
  payment_status: 'unpaid' | 'partial_paid' | 'paid'
  payment_status_name: string
  payment_term?: string
  sales_person?: string
  contact_person?: string
  contact_phone?: string
  remarks?: string
  items: SalesOrderItem[]
  created_by: string
  approved_by?: string
  approved_at?: string
  created_at: string
  updated_at: string
}

/** 销售订单明细 */
export interface SalesOrderItem {
  id: number
  order_id: number
  line_no: number
  product_code: string
  product_name: string
  specification?: string
  unit: string
  quantity: number
  delivered_quantity: number
  unit_price: number
  tax_rate: number
  tax_amount: number
  amount: number
  warehouse_code?: string
  expected_delivery_date?: string
  remarks?: string
}

/** 销售发货单 */
export interface SalesDelivery {
  id: number
  delivery_no: string
  order_id: number
  order_no: string
  customer_code: string
  customer_name: string
  warehouse_code: string
  warehouse_name: string
  delivery_date: string
  delivery_address: string
  status: 'draft' | 'confirmed' | 'shipped' | 'completed'
  status_name: string
  tracking_no?: string
  carrier?: string
  total_quantity: number
  remarks?: string
  items: SalesDeliveryItem[]
  created_by: string
  confirmed_by?: string
  confirmed_at?: string
  shipped_at?: string
  completed_at?: string
  created_at: string
}

/** 销售发货明细 */
export interface SalesDeliveryItem {
  id: number
  delivery_id: number
  order_item_id: number
  product_code: string
  product_name: string
  unit: string
  ordered_quantity: number
  delivery_quantity: number
  batch_no?: string
  remarks?: string
}

/** 销售退货单 */
export interface SalesReturn {
  id: number
  return_no: string
  order_id?: number
  order_no?: string
  delivery_id?: number
  delivery_no?: string
  customer_code: string
  customer_name: string
  warehouse_code: string
  warehouse_name: string
  return_date: string
  status: 'draft' | 'pending' | 'approved' | 'received' | 'completed' | 'rejected'
  status_name: string
  return_reason: string
  total_quantity: number
  total_amount: number
  refund_status: 'pending' | 'refunded' | 'rejected'
  refund_status_name: string
  refund_amount: number
  remarks?: string
  items: SalesReturnItem[]
  created_by: string
  approved_by?: string
  approved_at?: string
  created_at: string
}

/** 销售退货明细 */
export interface SalesReturnItem {
  id: number
  return_id: number
  product_code: string
  product_name: string
  unit: string
  return_quantity: number
  received_quantity: number
  unit_price: number
  amount: number
  quality_status?: 'good' | 'damaged' | 'defective'
  return_reason?: string
  remarks?: string
}

/** 销售查询参数 */
export interface SalesQueryParams {
  order_no?: string
  customer_code?: string
  status?: string
  sales_person?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

/** 销售统计 */
export interface SalesStats {
  total_orders: number
  total_amount: number
  pending_orders: number
  pending_amount: number
  completed_orders: number
  completed_amount: number
  this_month_orders: number
  this_month_amount: number
  last_month_orders: number
  last_month_amount: number
  month_over_month_rate: number
  average_order_value: number
}

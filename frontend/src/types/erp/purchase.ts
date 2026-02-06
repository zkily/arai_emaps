/**
 * 采购管理类型定义
 */

/** 采购订单 */
export interface PurchaseOrder {
  id: number
  order_no: string
  supplier_code: string
  supplier_name: string
  order_date: string
  expected_delivery_date?: string
  warehouse_code: string
  warehouse_name: string
  status: 'draft' | 'pending' | 'approved' | 'partial_received' | 'completed' | 'cancelled'
  status_name: string
  currency: string
  exchange_rate: number
  subtotal: number
  tax_rate: number
  tax_amount: number
  discount_rate: number
  discount_amount: number
  total_amount: number
  paid_amount: number
  payment_status: 'unpaid' | 'partial_paid' | 'paid'
  payment_status_name: string
  payment_term?: string
  contact_person?: string
  contact_phone?: string
  delivery_address?: string
  remarks?: string
  items: PurchaseOrderItem[]
  created_by: string
  approved_by?: string
  approved_at?: string
  created_at: string
  updated_at: string
}

/** 采购订单明细 */
export interface PurchaseOrderItem {
  id: number
  order_id: number
  line_no: number
  product_code: string
  product_name: string
  specification?: string
  unit: string
  quantity: number
  received_quantity: number
  unit_price: number
  tax_rate: number
  tax_amount: number
  amount: number
  expected_delivery_date?: string
  remarks?: string
}

/** 采购收货单 */
export interface PurchaseReceipt {
  id: number
  receipt_no: string
  order_id: number
  order_no: string
  supplier_code: string
  supplier_name: string
  warehouse_code: string
  warehouse_name: string
  receipt_date: string
  status: 'draft' | 'confirmed'
  status_name: string
  total_quantity: number
  remarks?: string
  items: PurchaseReceiptItem[]
  created_by: string
  confirmed_by?: string
  confirmed_at?: string
  created_at: string
}

/** 采购收货明细 */
export interface PurchaseReceiptItem {
  id: number
  receipt_id: number
  order_item_id: number
  product_code: string
  product_name: string
  unit: string
  ordered_quantity: number
  received_quantity: number
  location?: string
  batch_no?: string
  production_date?: string
  expiry_date?: string
  remarks?: string
}

/** 采购退货单 */
export interface PurchaseReturn {
  id: number
  return_no: string
  order_id?: number
  order_no?: string
  receipt_id?: number
  receipt_no?: string
  supplier_code: string
  supplier_name: string
  warehouse_code: string
  warehouse_name: string
  return_date: string
  status: 'draft' | 'pending' | 'approved' | 'completed' | 'rejected'
  status_name: string
  return_reason: string
  total_quantity: number
  total_amount: number
  remarks?: string
  items: PurchaseReturnItem[]
  created_by: string
  approved_by?: string
  approved_at?: string
  created_at: string
}

/** 采购退货明细 */
export interface PurchaseReturnItem {
  id: number
  return_id: number
  product_code: string
  product_name: string
  unit: string
  return_quantity: number
  unit_price: number
  amount: number
  return_reason?: string
  remarks?: string
}

/** 采购查询参数 */
export interface PurchaseQueryParams {
  order_no?: string
  supplier_code?: string
  status?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

/** 采购统计 */
export interface PurchaseStats {
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
}

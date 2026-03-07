/**
 * 供应商管理类型定义
 */

/** 供应商 */
export interface Supplier {
  id: number
  supplier_code: string
  supplier_name: string
  supplier_name_kana?: string
  supplier_type: 'manufacturer' | 'distributor' | 'service' | 'other'
  supplier_type_name: string
  category?: string
  tax_id?: string
  postal_code?: string
  address?: string
  phone?: string
  fax?: string
  email?: string
  website?: string
  bank_name?: string
  bank_branch?: string
  bank_account_type?: string
  bank_account_no?: string
  bank_account_name?: string
  payment_term?: string
  currency: string
  credit_limit?: number
  rating?: 'A' | 'B' | 'C' | 'D'
  is_active: boolean
  remarks?: string
  contacts?: SupplierContact[]
  created_at: string
  updated_at: string
}

/** 供应商联系人 */
export interface SupplierContact {
  id: number
  supplier_id: number
  contact_name: string
  department?: string
  position?: string
  phone?: string
  mobile?: string
  email?: string
  is_primary: boolean
  remarks?: string
  created_at: string
  updated_at: string
}

/** 供应商评价 */
export interface SupplierEvaluation {
  id: number
  supplier_id: number
  supplier_code: string
  supplier_name: string
  evaluation_period: string
  year: number
  quarter: number
  quality_score: number
  delivery_score: number
  price_score: number
  service_score: number
  total_score: number
  rating: 'A' | 'B' | 'C' | 'D'
  evaluator: string
  evaluation_date: string
  remarks?: string
  created_at: string
}

/** 供应商查询参数 */
export interface SupplierQueryParams {
  keyword?: string
  supplier_type?: string
  category?: string
  rating?: string
  is_active?: boolean
  page?: number
  page_size?: number
}

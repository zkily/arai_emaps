/**
 * 基础数据管理类型定义
 */

/** 仓库 */
export interface Warehouse {
  id: number
  warehouse_code: string
  warehouse_name: string
  warehouse_type: 'material' | 'product' | 'semi_finished' | 'defective' | 'transit'
  warehouse_type_name: string
  address?: string
  manager?: string
  phone?: string
  capacity?: number
  is_active: boolean
  remarks?: string
  created_at: string
  updated_at: string
}

/** 产品分类 */
export interface ProductCategory {
  id: number
  category_code: string
  category_name: string
  parent_id?: number
  parent_name?: string
  level: number
  sort_order: number
  is_active: boolean
  remarks?: string
  children?: ProductCategory[]
  created_at: string
  updated_at: string
}

/** 单位 */
export interface Unit {
  id: number
  unit_code: string
  unit_name: string
  unit_name_en?: string
  is_base_unit: boolean
  base_unit_id?: number
  conversion_rate?: number
  is_active: boolean
  created_at: string
  updated_at: string
}

/** 付款条款 */
export interface PaymentTerm {
  id: number
  term_code: string
  term_name: string
  days: number
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

/** 币种 */
export interface Currency {
  id: number
  currency_code: string
  currency_name: string
  symbol: string
  exchange_rate: number
  decimal_places: number
  is_base_currency: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

/** 系统配置 */
export interface SystemConfig {
  id: number
  config_key: string
  config_value: string
  config_type: 'string' | 'number' | 'boolean' | 'json'
  description?: string
  is_system: boolean
  created_at: string
  updated_at: string
}

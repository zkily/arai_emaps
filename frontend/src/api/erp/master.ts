/**
 * 基础数据管理API
 */
import request from '@/utils/request'
import type {
  Warehouse,
  ProductCategory,
  Unit,
  PaymentTerm,
  Currency
} from '@/types/erp/master'

const BASE_URL = '/api/erp/master'

// ========== 仓库管理 ==========

/** 获取仓库列表 */
export const getWarehouseList = (params?: {
  keyword?: string
  is_active?: boolean
  page?: number
  page_size?: number
}) => {
  return request.get<{ items: Warehouse[]; total: number }>(`${BASE_URL}/warehouses`, { params })
}

/** 获取仓库详情 */
export const getWarehouseById = (id: number) => {
  return request.get<Warehouse>(`${BASE_URL}/warehouses/${id}`)
}

/** 创建仓库 */
export const createWarehouse = (data: Partial<Warehouse>) => {
  return request.post<Warehouse>(`${BASE_URL}/warehouses`, data)
}

/** 更新仓库 */
export const updateWarehouse = (id: number, data: Partial<Warehouse>) => {
  return request.put<Warehouse>(`${BASE_URL}/warehouses/${id}`, data)
}

/** 删除仓库 */
export const deleteWarehouse = (id: number) => {
  return request.delete(`${BASE_URL}/warehouses/${id}`)
}

/** 获取仓库选项列表 */
export const getWarehouseOptions = () => {
  return request.get<Array<{ code: string; name: string; id: number }>>(`${BASE_URL}/warehouses/options`)
}

// ========== 产品分类管理 ==========

/** 获取产品分类树 */
export const getProductCategoryTree = () => {
  return request.get<ProductCategory[]>(`${BASE_URL}/categories/tree`)
}

/** 获取产品分类列表 */
export const getProductCategoryList = (params?: {
  parent_id?: number
  keyword?: string
}) => {
  return request.get<ProductCategory[]>(`${BASE_URL}/categories`, { params })
}

/** 创建产品分类 */
export const createProductCategory = (data: Partial<ProductCategory>) => {
  return request.post<ProductCategory>(`${BASE_URL}/categories`, data)
}

/** 更新产品分类 */
export const updateProductCategory = (id: number, data: Partial<ProductCategory>) => {
  return request.put<ProductCategory>(`${BASE_URL}/categories/${id}`, data)
}

/** 删除产品分类 */
export const deleteProductCategory = (id: number) => {
  return request.delete(`${BASE_URL}/categories/${id}`)
}

// ========== 单位管理 ==========

/** 获取单位列表 */
export const getUnitList = (params?: {
  keyword?: string
  is_active?: boolean
}) => {
  return request.get<Unit[]>(`${BASE_URL}/units`, { params })
}

/** 创建单位 */
export const createUnit = (data: Partial<Unit>) => {
  return request.post<Unit>(`${BASE_URL}/units`, data)
}

/** 更新单位 */
export const updateUnit = (id: number, data: Partial<Unit>) => {
  return request.put<Unit>(`${BASE_URL}/units/${id}`, data)
}

/** 删除单位 */
export const deleteUnit = (id: number) => {
  return request.delete(`${BASE_URL}/units/${id}`)
}

// ========== 付款条款管理 ==========

/** 获取付款条款列表 */
export const getPaymentTermList = (params?: {
  is_active?: boolean
}) => {
  return request.get<PaymentTerm[]>(`${BASE_URL}/payment-terms`, { params })
}

/** 创建付款条款 */
export const createPaymentTerm = (data: Partial<PaymentTerm>) => {
  return request.post<PaymentTerm>(`${BASE_URL}/payment-terms`, data)
}

/** 更新付款条款 */
export const updatePaymentTerm = (id: number, data: Partial<PaymentTerm>) => {
  return request.put<PaymentTerm>(`${BASE_URL}/payment-terms/${id}`, data)
}

/** 删除付款条款 */
export const deletePaymentTerm = (id: number) => {
  return request.delete(`${BASE_URL}/payment-terms/${id}`)
}

// ========== 币种管理 ==========

/** 获取币种列表 */
export const getCurrencyList = (params?: {
  is_active?: boolean
}) => {
  return request.get<Currency[]>(`${BASE_URL}/currencies`, { params })
}

/** 创建币种 */
export const createCurrency = (data: Partial<Currency>) => {
  return request.post<Currency>(`${BASE_URL}/currencies`, data)
}

/** 更新币种 */
export const updateCurrency = (id: number, data: Partial<Currency>) => {
  return request.put<Currency>(`${BASE_URL}/currencies/${id}`, data)
}

/** 更新汇率 */
export const updateExchangeRate = (id: number, exchange_rate: number) => {
  return request.patch(`${BASE_URL}/currencies/${id}/rate`, { exchange_rate })
}

// ========== 序列号生成 ==========

/** 获取新的单据编号 */
export const generateDocumentNumber = (docType: 'PO' | 'SO' | 'DO' | 'PR' | 'SR' | 'INV' | 'ADJ') => {
  return request.get<{ number: string }>(`${BASE_URL}/sequence/${docType}`)
}

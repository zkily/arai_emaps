/**
 * 供应商管理API
 */
import request from '@/utils/request'
import type {
  Supplier,
  SupplierContact,
  SupplierEvaluation,
  SupplierQueryParams
} from '@/types/erp/supplier'

const BASE_URL = '/api/erp/suppliers'

// ========== 供应商基本信息 ==========

/** 获取供应商列表 */
export const getSupplierList = (params?: SupplierQueryParams) => {
  return request.get<{ items: Supplier[]; total: number }>(BASE_URL, { params })
}

/** 获取供应商详情 */
export const getSupplierById = (id: number) => {
  return request.get<Supplier>(`${BASE_URL}/${id}`)
}

/** 按编码获取供应商 */
export const getSupplierByCode = (code: string) => {
  return request.get<Supplier>(`${BASE_URL}/code/${code}`)
}

/** 创建供应商 */
export const createSupplier = (data: Partial<Supplier>) => {
  return request.post<Supplier>(BASE_URL, data)
}

/** 更新供应商 */
export const updateSupplier = (id: number, data: Partial<Supplier>) => {
  return request.put<Supplier>(`${BASE_URL}/${id}`, data)
}

/** 删除供应商 */
export const deleteSupplier = (id: number) => {
  return request.delete(`${BASE_URL}/${id}`)
}

/** 启用/禁用供应商 */
export const toggleSupplierStatus = (id: number, is_active: boolean) => {
  return request.patch(`${BASE_URL}/${id}/status`, { is_active })
}

// ========== 供应商联系人 ==========

/** 获取供应商联系人列表 */
export const getSupplierContacts = (supplierId: number) => {
  return request.get<SupplierContact[]>(`${BASE_URL}/${supplierId}/contacts`)
}

/** 添加供应商联系人 */
export const addSupplierContact = (supplierId: number, data: Partial<SupplierContact>) => {
  return request.post<SupplierContact>(`${BASE_URL}/${supplierId}/contacts`, data)
}

/** 更新供应商联系人 */
export const updateSupplierContact = (supplierId: number, contactId: number, data: Partial<SupplierContact>) => {
  return request.put<SupplierContact>(`${BASE_URL}/${supplierId}/contacts/${contactId}`, data)
}

/** 删除供应商联系人 */
export const deleteSupplierContact = (supplierId: number, contactId: number) => {
  return request.delete(`${BASE_URL}/${supplierId}/contacts/${contactId}`)
}

// ========== 供应商评价 ==========

/** 获取供应商评价列表 */
export const getSupplierEvaluations = (supplierId: number, params?: {
  year?: number
  quarter?: number
}) => {
  return request.get<SupplierEvaluation[]>(`${BASE_URL}/${supplierId}/evaluations`, { params })
}

/** 创建供应商评价 */
export const createSupplierEvaluation = (supplierId: number, data: Partial<SupplierEvaluation>) => {
  return request.post<SupplierEvaluation>(`${BASE_URL}/${supplierId}/evaluations`, data)
}

/** 获取供应商统计信息 */
export const getSupplierStats = (supplierId: number, params?: {
  start_date?: string
  end_date?: string
}) => {
  return request.get<{
    total_purchase_amount: number
    total_order_count: number
    average_delivery_days: number
    quality_rate: number
    on_time_rate: number
  }>(`${BASE_URL}/${supplierId}/stats`, { params })
}

// ========== 供应商产品 ==========

/** 获取供应商供应的产品列表 */
export const getSupplierProducts = (supplierId: number) => {
  return request.get<Array<{
    product_code: string
    product_name: string
    unit_price: number
    min_order_quantity: number
    lead_time_days: number
  }>>(`${BASE_URL}/${supplierId}/products`)
}

/** 关联供应商与产品 */
export const linkSupplierProduct = (supplierId: number, data: {
  product_code: string
  unit_price: number
  min_order_quantity?: number
  lead_time_days?: number
}) => {
  return request.post(`${BASE_URL}/${supplierId}/products`, data)
}

/** 取消供应商与产品关联 */
export const unlinkSupplierProduct = (supplierId: number, productCode: string) => {
  return request.delete(`${BASE_URL}/${supplierId}/products/${productCode}`)
}

// ========== 供应商下拉选项 ==========

/** 获取供应商选项列表（用于下拉框） */
export const getSupplierOptions = () => {
  return request.get<Array<{
    code: string
    name: string
    id: number
  }>>(`${BASE_URL}/options`)
}

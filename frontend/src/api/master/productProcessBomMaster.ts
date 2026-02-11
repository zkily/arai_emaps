/**
 * 製品工程BOMマスタ API
 */
import request from '@/shared/api/request'

export interface ProductProcessBOM {
  product_cd: number
  product_name?: string
  min_stock_days?: number
  safety_stock_days?: number
  material_process?: boolean | number
  material_process_lt?: number
  cuting_process?: boolean | number
  cuting_process_lt?: number
  chamfering_process?: boolean | number
  chamfering_process_lt?: number
  swaging_process?: boolean | number
  swaging_process_lt?: number
  forming_process?: boolean | number
  forming_process_lt?: number
  plating_process?: boolean | number
  plating_process_lt?: number
  outsourced_plating_process?: boolean | number
  outsourced_plating_process_lt?: number
  welding_process?: boolean | number
  welding_process_lt?: number
  outsourced_welding_process?: boolean | number
  outsourced_welding_process_lt?: number
  inspection_process?: boolean | number
  inspection_process_lt?: number
  outsourced_warehouse_process?: boolean | number
  outsourced_warehouse_process_lt?: number
  pre_plating_welding?: boolean | number
  post_inspection_welding?: boolean | number
  post_inspection_welding_lt?: number
  is_discontinued?: boolean | number
}

export interface ProductProcessBOMListParams {
  page?: number
  limit?: number
  keyword?: string
  sort_by?: string
  sort_order?: string
}

export interface ProductProcessBOMListResponse {
  success?: boolean
  data?: {
    list: ProductProcessBOM[]
    total: number
    active_count?: number
    discontinued_count?: number
  }
  list?: ProductProcessBOM[]
  total?: number
  active_count?: number
  discontinued_count?: number
}

const BASE = '/api/master/product-process-bom'

export function fetchProductProcessBOMList(
  params?: ProductProcessBOMListParams
): Promise<ProductProcessBOMListResponse> {
  return request.get(BASE, { params }) as Promise<ProductProcessBOMListResponse>
}

export function fetchProductProcessBOMById(productCd: number): Promise<ProductProcessBOM> {
  return request.get(`${BASE}/${productCd}`) as Promise<ProductProcessBOM>
}

export function updateProductProcessBOM(
  productCd: number,
  data: Partial<ProductProcessBOM>
): Promise<ProductProcessBOM> {
  return request.put(`${BASE}/${productCd}`, data) as Promise<ProductProcessBOM>
}

export function deleteProductProcessBOM(productCd: number): Promise<{ message: string }> {
  return request.delete(`${BASE}/${productCd}`) as Promise<{ message: string }>
}

export function syncProductInfo(): Promise<{
  success?: boolean
  data?: {
    inserted_count?: number
    updated_count?: number
    total_processed?: number
    message?: string
  }
}> {
  return request.post(`${BASE}/sync`) as Promise<any>
}

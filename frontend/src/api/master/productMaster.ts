/**
 * 製品マスタ API
 */
import request from '@/shared/api/request'
import type { Product } from '@/types/master'

export interface ProductListParams {
  keyword?: string
  category?: string
  product_type?: string
  status?: string
  product_cd?: string
  material_cd?: string
  route_cd?: string
  location_cd?: string
  destination_cd?: string
  page?: number
  pageSize?: number
}

export interface ProductListResponse {
  success?: boolean
  data?: { list: Product[]; total: number }
  list?: Product[]
  total?: number
}

export function getProductList(params: ProductListParams): Promise<ProductListResponse> {
  return request.get('/api/master/products', { params }) as Promise<ProductListResponse>
}

/** 月注文一括登録用：指定納入先の製品のみ（destination_cd=納入先、status=active、product_type=量産品） */
export function getProductsByDestinationForBatch(destinationCd: string): Promise<ProductListResponse> {
  return request.get(`/api/master/products/by-destination/${encodeURIComponent(destinationCd)}`) as Promise<ProductListResponse>
}

export function getMaxProductCd(): Promise<number> {
  return request.get('/api/master/products/max-cd') as Promise<number>
}

export function createProduct(data: Product): Promise<Product> {
  return request.post('/api/master/products', data) as Promise<Product>
}

export function updateProduct(data: Product): Promise<Product> {
  if (!data.id) return Promise.reject(new Error('id is required'))
  return request.put(`/api/master/products/${data.id}`, data) as Promise<Product>
}

export function deleteProduct(id: number): Promise<{ message: string }> {
  return request.delete(`/api/master/products/${id}`) as Promise<{ message: string }>
}

export interface ExportProductCsvResult {
  success: boolean
  message?: string
  fileName?: string
  csvFilePath?: string
  rowCount?: number
}

export async function exportProductToCSV(
  rows: Array<{ product_cd?: string; product_name?: string; unit_per_box?: number }>
): Promise<ExportProductCsvResult> {
  return request.post('/api/master/products/export-csv', rows) as Promise<ExportProductCsvResult>
}

/** 端材長一括再計算（材料名末尾4桁・cut_length・take_count より scrap_length を更新） */
export interface RecalculateScrapLengthResult {
  success?: boolean
  updated?: number
  skipped?: number
  total?: number
}

export function recalculateProductScrapLength(): Promise<RecalculateScrapLengthResult> {
  return request.post('/api/master/products/recalculate-scrap-length') as Promise<RecalculateScrapLengthResult>
}

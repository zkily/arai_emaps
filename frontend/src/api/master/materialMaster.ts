/**
 * 材料マスタ API
 */
import request from '@/shared/api/request'
import type { Material } from '@/types/master'

export interface MaterialListParams {
  keyword?: string
  status?: number
  material_type?: string
  supply_classification?: string
  usegae?: string
  storage_location?: string
  page?: number
  pageSize?: number
}

export interface MaterialListResponse {
  success?: boolean
  data?: { list: Material[]; total: number }
  list?: Material[]
  total?: number
}

export function getMaterialList(params?: MaterialListParams): Promise<MaterialListResponse> {
  return request.get('/api/master/materials', { params }) as Promise<MaterialListResponse>
}

export function getMaxMaterialCd(): Promise<{ max_code: number }> {
  return request.get('/api/master/materials/max-cd') as Promise<{ max_code: number }>
}

export function getMaterialById(id: number): Promise<Material> {
  return request.get(`/api/master/materials/${id}`) as Promise<Material>
}

export function createMaterial(data: Material): Promise<Material> {
  return request.post('/api/master/materials', data) as Promise<Material>
}

export function updateMaterial(data: Material): Promise<Material> {
  if (!data.id) return Promise.reject(new Error('id is required'))
  return request.put(`/api/master/materials/${data.id}`, data) as Promise<Material>
}

export function deleteMaterialById(id: number): Promise<{ message: string }> {
  return request.delete(`/api/master/materials/${id}`) as Promise<{ message: string }>
}

export async function exportMaterialToCSV(
  rows: Array<{ material_cd?: string; material_name?: string }>
): Promise<void> {
  const res = await request.post('/api/master/materials/export-csv', rows, {
    responseType: 'blob',
  })
  const blob = res as unknown as Blob
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'materials.csv'
  a.click()
  window.URL.revokeObjectURL(url)
}

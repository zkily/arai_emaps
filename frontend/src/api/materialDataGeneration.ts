/**
 * 材料在庫データ生成 API
 * backend の `/api/material-data-generation/generate` に対応
 */
import request from '@/shared/api/request'

export interface MaterialDataGenerationRequest {
  start_date: string
  end_date: string
  overwrite_existing?: boolean
}

/**
 * 材料在庫データ生成
 * POST /api/material-data-generation/generate
 */
export function generateMaterialStockData(params: MaterialDataGenerationRequest) {
  return request.post('/api/material-data-generation/generate', params)
}

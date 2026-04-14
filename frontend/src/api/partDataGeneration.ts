import request from '@/shared/api/request'

export interface PartDataGenerationRequest {
  start_date: string
  end_date: string
  overwrite_existing?: boolean
}

export function generatePartStockData(params: PartDataGenerationRequest) {
  return request.post('/api/part-data-generation/generate', params)
}

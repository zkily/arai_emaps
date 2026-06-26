/**
 * 理論在庫 vs 棚卸在庫 比較 API
 */
import request from '@/shared/api/request'

export type ComparisonStatus = 'match' | 'only_theoretical' | 'only_stocktake' | 'mismatch'

export interface ComparisonKpi {
  theoretical_qty_total: number
  stocktake_qty_total: number
  diff_qty_total: number
  item_count: number
  matched_count: number
  mismatch_count: number
  only_theoretical_count: number
  only_stocktake_count: number
  match_rate: number
}

export interface ComparisonSummaryRow {
  process_cd: string
  process_name: string
  theoretical_qty: number
  stocktake_qty: number
  diff_qty: number
  diff_rate: number | null
  item_count: number
  matched_count: number
  only_theoretical_count: number
  only_stocktake_count: number
  mismatch_count: number
  match_rate: number
}

export interface ComparisonDetailRow {
  product_cd: string
  product_name: string
  process_cd: string
  process_name: string
  theoretical_qty: number
  stocktake_qty: number
  diff_qty: number
  status: ComparisonStatus
}

export interface ProductComparisonParams {
  as_of: string
  process_cd?: string
  product_cd?: string
  keyword?: string
  view?: 'summary' | 'detail'
  only_diff?: boolean
  page?: number
  limit?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface ProductComparisonResponse {
  as_of: string
  view: 'summary' | 'detail'
  list: ComparisonSummaryRow[] | ComparisonDetailRow[]
  total?: number
  page?: number
  limit?: number
  kpi: ComparisonKpi
}

export const inventoryComparisonApi = {
  async getProductComparison(params: ProductComparisonParams): Promise<ProductComparisonResponse> {
    const res = (await request.get('/api/erp/inventory-comparison/product', {
      params: {
        as_of: params.as_of,
        process_cd:
          params.process_cd && params.process_cd !== 'all' ? params.process_cd : undefined,
        product_cd: params.product_cd?.trim() || undefined,
        keyword: params.keyword?.trim() || undefined,
        view: params.view ?? 'summary',
        only_diff: params.only_diff ?? false,
        page: params.page,
        limit: params.limit,
        sort_by: params.sort_by,
        sort_order: params.sort_order,
      },
    })) as { success?: boolean; data?: ProductComparisonResponse }
    const data = res?.data
    if (!data) {
      return {
        as_of: params.as_of,
        view: params.view ?? 'summary',
        list: [],
        kpi: {
          theoretical_qty_total: 0,
          stocktake_qty_total: 0,
          diff_qty_total: 0,
          item_count: 0,
          matched_count: 0,
          mismatch_count: 0,
          only_theoretical_count: 0,
          only_stocktake_count: 0,
          match_rate: 0,
        },
      }
    }
    return data
  },
}

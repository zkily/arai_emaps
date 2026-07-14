/**
 * 生産管理 vs 製造：不良・廃棄合算データ突合 API
 */
import request from '@/shared/api/request'

export type DefectScrapComparisonStatus =
  | 'match'
  | 'mismatch'
  | 'only_summary'
  | 'only_source'
  | 'not_comparable'
  | 'plating_daily_only'

export interface DefectScrapComparisonKpi {
  summary_total: number
  source_total: number
  total_diff: number
  summary_defect_total?: number
  source_defect_total?: number
  summary_scrap_total?: number
  source_scrap_total?: number
  item_count: number
  matched_count: number
  mismatch_count: number
  only_summary_count: number
  only_source_count: number
  not_comparable_count: number
  match_rate: number
}

export interface DefectScrapComparisonSummaryRow {
  process_cd: string
  process_name: string
  summary_total: number
  source_total: number
  total_diff: number
  item_count: number
  matched_count: number
  mismatch_count: number
  only_summary_count: number
  only_source_count: number
  match_rate: number
  source_note?: string
}

export interface DefectScrapComparisonMonthlyRow {
  year_month: string
  label: string
  summary_total: number
  source_total: number
  total_diff: number
  match_rate: number
  item_count: number
  mismatch_count: number
}

export interface DefectScrapComparisonDetailRow {
  product_cd: string
  product_name: string
  production_day: string
  process_cd: string
  process_name: string
  summary_total: number
  source_total: number | null
  total_diff: number | null
  summary_defect?: number
  source_defect?: number | null
  summary_scrap?: number
  source_scrap?: number | null
  status: DefectScrapComparisonStatus
  source_note?: string
}

export interface PlatingDailyRow {
  production_day: string
  summary_total: number
  source_total: number
  total_diff: number
  summary_defect?: number
  source_defect?: number
  summary_scrap?: number
  source_scrap?: number | null
  status: DefectScrapComparisonStatus
}

export interface DefectScrapComparisonParams {
  startDate: string
  endDate: string
  processCd?: string
  productCd?: string
  onlyDiff?: boolean
  view?: 'summary' | 'detail' | 'monthly'
  page?: number
  limit?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface DefectScrapComparisonResponse {
  start_date: string
  end_date: string
  view: 'summary' | 'detail' | 'monthly'
  list:
    | DefectScrapComparisonSummaryRow[]
    | DefectScrapComparisonDetailRow[]
    | DefectScrapComparisonMonthlyRow[]
  plating_daily: PlatingDailyRow[]
  total?: number
  page?: number
  limit?: number
  kpi: DefectScrapComparisonKpi
}

const BASE = '/api/database/defect-scrap-comparison'

const EMPTY_KPI: DefectScrapComparisonKpi = {
  summary_total: 0,
  source_total: 0,
  total_diff: 0,
  item_count: 0,
  matched_count: 0,
  mismatch_count: 0,
  only_summary_count: 0,
  only_source_count: 0,
  not_comparable_count: 0,
  match_rate: 0,
}

export const defectScrapComparisonApi = {
  async getComparison(params: DefectScrapComparisonParams): Promise<DefectScrapComparisonResponse> {
    const res = (await request.get(BASE, {
      params: {
        startDate: params.startDate,
        endDate: params.endDate,
        processCd:
          params.processCd && params.processCd !== 'all' ? params.processCd : undefined,
        productCd: params.productCd?.trim() || undefined,
        onlyDiff: params.onlyDiff ?? false,
        view: params.view ?? 'summary',
        page: params.page,
        limit: params.limit,
        sort_by: params.sort_by,
        sort_order: params.sort_order,
      },
    })) as { success?: boolean; data?: DefectScrapComparisonResponse }

    const data = res?.data
    if (!data) {
      return {
        start_date: params.startDate,
        end_date: params.endDate,
        view: params.view ?? 'summary',
        list: [],
        plating_daily: [],
        kpi: { ...EMPTY_KPI },
      }
    }
    return data
  },
}

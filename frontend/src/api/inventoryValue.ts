/**
 * 棚卸金額・分析 API（バックエンド実装済み）
 */
import request from '@/shared/api/request'
import { fetchProcesses } from '@/api/master/processMaster'

export interface InventoryValueParams {
  startDate?: string
  endDate?: string
  processCode?: string
}

export interface InventoryValueData {
  id?: number
  item_type?: string
  product_cd?: string
  product_name?: string
  unit_price?: number
  [key: string]: unknown
}

export const inventoryValueApi = {
  async getInventoryValueSummary(params: InventoryValueParams) {
    try {
      const res = (await request.get('/api/erp/inventory-value/summary', {
        params: {
          start_date: params.startDate,
          end_date: params.endDate,
          process_cd:
            params.processCode && params.processCode !== 'all' ? params.processCode : undefined,
        },
      })) as { success?: boolean; data?: unknown }
      const inner = res && typeof res === 'object' && 'data' in res ? (res as { data: unknown }).data : res
      return { data: inner }
    } catch {
      return {
        data: {
          total: { total_amount: 0, material_amount: 0, component_amount: 0, stay_amount: 0 },
          byType: [],
          byProcess: [],
        },
      }
    }
  },

  async getProcessList() {
    try {
      const res = await fetchProcesses({ page: 1, pageSize: 5000 })
      const r = res as { data?: { list?: unknown[] }; list?: unknown[] }
      const list = r?.data?.list ?? r?.list ?? []
      return { data: list }
    } catch {
      return { data: [] }
    }
  },

  /** 明細一覧（バックエンド: page, limit, item_type, process_cd, run_id） */
  /** 実在庫テーブル由来の一覧（材料 material_stock / 部品 part_stock / 製品 production_summarys） */
  async getStockPanel(params: {
    tab: 'material' | 'part' | 'product'
    as_of: string
    process_cd?: string
    /** 材料CD / 部品CD / 製品CD（完全一致） */
    product_cd?: string
    page?: number
    limit?: number
    sort_by?: string
    sort_order?: string
  }) {
    try {
      const page = params.page ?? 1
      const limit = params.limit ?? 50
      const res = (await request.get('/api/erp/inventory-value/stock-panel', {
        params: {
          tab: params.tab,
          as_of: params.as_of,
          process_cd:
            params.process_cd && params.process_cd !== 'all' ? params.process_cd : undefined,
          product_cd: params.product_cd?.trim() ? params.product_cd.trim() : undefined,
          page,
          limit,
          sort_by: params.sort_by,
          sort_order: params.sort_order,
        },
      })) as {
        success?: boolean
        data?: { list?: unknown[]; total?: number; as_of?: string; sum_total_value?: number }
      }
      const payload = res?.data ?? { list: [], total: 0 }
      return {
        data: {
          list: payload.list ?? [],
          total: payload.total ?? 0,
          as_of: payload.as_of,
          sum_total_value:
            payload.sum_total_value !== undefined && payload.sum_total_value !== null
              ? Number(payload.sum_total_value)
              : undefined,
        },
      }
    } catch {
      return { data: { list: [], total: 0 } }
    }
  },

  async getValueList(params: {
    run_id?: number
    item_type?: string
    process_cd?: string
    page?: number
    limit?: number
    /** 旧 UI 互換 */
    pageSize?: number
  }) {
    try {
      const page = params.page ?? 1
      const limit = params.limit ?? params.pageSize ?? 50
      const res = (await request.get('/api/erp/inventory-value/details', {
        params: {
          run_id: params.run_id,
          item_type: params.item_type,
          process_cd:
            params.process_cd && params.process_cd !== 'all' ? params.process_cd : undefined,
          page,
          limit,
        },
      })) as { success?: boolean; data?: { list?: unknown[]; total?: number } }
      const payload = res?.data ?? { list: [], total: 0 }
      const list = (payload.list ?? []).map((raw: unknown) => {
        const row = raw as Record<string, unknown>
        const amount = row.amount ?? row.total_value
        const qty = row.quantity
        const quantity = typeof qty === 'number' ? qty : Number(qty) || 0
        // バックエンドが返す unit_price を最優先（部品は parts、他は累計スナップショット等）
        const explicit =
          row.unit_price !== undefined && row.unit_price !== null && row.unit_price !== ''
            ? row.unit_price
            : undefined
        const unitPriceSnapshot =
          explicit !== undefined ? explicit : (row.unit_price_snapshot ?? row.unit_price)
        const unitPriceByAmount = amount != null && quantity > 0 ? Number(amount) / quantity : null
        // 既存データ互換のため unit_price が無い場合のみ amount/qty を使用
        const unitPrice = unitPriceSnapshot ?? unitPriceByAmount ?? null
        return {
          ...row,
          quantity,
          unit_price: unitPrice != null ? Number(unitPrice) : null,
          total_value:
            amount != null
              ? Number(amount)
              : row.quantity != null && unitPrice != null
                ? Number(row.quantity) * Number(unitPrice)
                : 0,
        }
      })
      return { data: { list, total: payload.total ?? 0 } }
    } catch {
      return { data: { list: [], total: 0 } }
    }
  },

  async calculateValue(params: { start_date: string; end_date: string; process_cd?: string }) {
    try {
      const body = {
        start_date: params.start_date,
        end_date: params.end_date,
        ...(params.process_cd && params.process_cd !== 'all' ? { process_cd: params.process_cd } : {}),
      }
      return (await request.post('/api/erp/inventory-value/calculate', body)) as {
        success?: boolean
        data?: unknown
        message?: string
      }
    } catch {
      return { success: false }
    }
  },

  async getErrors(runId?: number) {
    try {
      const res = await request.get('/api/erp/inventory-value/errors', {
        params: runId ? { run_id: runId } : {},
      }) as { data?: unknown }
      return { data: res?.data ?? [] }
    } catch {
      return { data: [] }
    }
  },

  async getRuns(params?: { page?: number; limit?: number }) {
    try {
      const res = await request.get('/api/erp/inventory-value/runs', { params }) as { data?: unknown }
      return { data: res?.data ?? { list: [], total: 0 } }
    } catch {
      return { data: { list: [], total: 0 } }
    }
  },

  async getShipmentUnits(params: {
    date?: string
    dates?: string[]
    destination_cd?: string
    destination_cds?: string[]
  }) {
    try {
      const res = (await request.get('/api/erp/inventory-value/shipment-units', {
        params: {
          date: params.date,
          dates: params.dates?.length ? params.dates.join(',') : undefined,
          destination_cd: params.destination_cd,
          destination_cds: params.destination_cds?.length ? params.destination_cds.join(',') : undefined,
        },
      })) as { success?: boolean; data?: { list?: { product_cd: string; confirmed_units_sum: number }[] } }
      return { data: { list: res?.data?.list ?? [] } }
    } catch {
      return { data: { list: [] } }
    }
  },

  async getDestinations() {
    try {
      const res = (await request.get('/api/erp/inventory-value/destinations')) as {
        success?: boolean
        data?: { list?: { destination_cd: string; destination_name: string }[] }
      }
      return { data: { list: res?.data?.list ?? [] } }
    } catch {
      return { data: { list: [] } }
    }
  },

  async exportExcel(_params: unknown) {
    return { data: new Blob() }
  },

  async getValueDetail(_id: number) {
    return { data: {} }
  },

  async updatePrice(_params: unknown) {
    return { ok: true }
  },

  async getItemDistributionChart(_params: unknown) {
    return { data: [] as { name: string; value: number }[] }
  },

  async getPeriodTrendChart(_params: unknown) {
    return {
      data: {
        dates: [] as string[],
        material: [] as number[],
        component: [] as number[],
        stay: [] as number[],
        total: [] as number[],
      },
    }
  },

  async getProcessComparisonChart(_params: unknown) {
    return {
      data: {
        processes: [] as string[],
        values: [] as number[],
        quantities: [] as number[],
      },
    }
  },

  async getHeatmapData(_params: unknown) {
    const z = Array.from({ length: 12 }, () => 0)
    return {
      data: {
        processes: ['—'],
        data: [z],
      },
    }
  },

  async getValueAnalysis(_params: unknown) {
    return { data: [] as unknown[] }
  },

  async getMonthlyInventoryReport(params: { as_of: string }) {
    try {
      const res = (await request.get('/api/erp/inventory-value/report/monthly', {
        params: { as_of: params.as_of },
      })) as { success?: boolean; data?: MonthlyInventoryReportData }
      return { success: res?.success ?? false, data: res?.data ?? null }
    } catch {
      return { success: false, data: null }
    }
  },
}

export interface MonthlyReportOverviewRow {
  label: string
  wip_qty: number
  wip_amount: number
  product_qty: number
  product_amount: number
  total_qty: number
  total_amount: number
}
export interface MonthlyReportOverview {
  rows: MonthlyReportOverviewRow[]
  totals: {
    wip_qty: number
    wip_amount: number
    product_qty: number
    product_amount: number
    total_qty: number
    total_amount: number
  }
}
export interface MonthlyReportPartMekaRow {
  kind: string
  part_cd: string
  part_name: string
  qty: number
  amount: number
}
export interface MonthlyReportPartNonMekaRow {
  kind: string
  qty: number
  amount: number
}
export interface MonthlyInventoryReportData {
  overview_by_kind: MonthlyReportOverview
  overview_by_category: MonthlyReportOverview
  parts_meka: { rows: MonthlyReportPartMekaRow[]; totals: { qty: number; amount: number } }
  parts_non_meka: { rows: MonthlyReportPartNonMekaRow[]; totals: { qty: number; amount: number } }
  meta: { as_of: string; month_label: string; printed_at: string; exchange_rate: number | null }
}

/**
 * 棚卸金額・分析 API（バックエンド未実装時はプレースホルダ）
 */
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

const emptySummary = () => ({
  total: {
    total_amount: 0,
    material_amount: 0,
    component_amount: 0,
    stay_amount: 0,
  },
  byType: [] as unknown[],
  byProcess: [] as unknown[],
})

export const inventoryValueApi = {
  async getInventoryValueSummary(_params: InventoryValueParams) {
    return { data: emptySummary() }
  },

  async getProcessList() {
    try {
      const res = await fetchProcesses({ page: 1, pageSize: 5000 })
      const list = (res as { list?: unknown[] })?.list ?? []
      return { data: list }
    } catch {
      return { data: [] }
    }
  },

  async getValueList(_params: any) {
    return { data: { list: [] as any[], total: 0 } }
  },

  async calculateValue(_params: any) {
    return { ok: true }
  },

  async exportExcel(_params: any) {
    return { data: new Blob() }
  },

  async getValueDetail(_id: number) {
    return { data: {} }
  },

  async updatePrice(_params: any) {
    return { ok: true }
  },

  async getItemDistributionChart(_params: any) {
    return { data: [] as { name: string; value: number }[] }
  },

  async getPeriodTrendChart(_params: any) {
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

  async getProcessComparisonChart(_params: any) {
    return {
      data: {
        processes: [] as string[],
        values: [] as number[],
        quantities: [] as number[],
      },
    }
  },

  async getHeatmapData(_params: any) {
    const z = Array.from({ length: 12 }, () => 0)
    return {
      data: {
        processes: ['—'],
        data: [z],
      },
    }
  },

  async getValueAnalysis(_params: any) {
    return { data: [] as any[] }
  },
}

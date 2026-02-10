/**
 * 下拉选项 API - 顧客・製品・納入先・材料・工程ルートの選択肢を取得
 */
import { getCustomers, getDestinations, getProducts } from '@/api/erp'
import { getProductList } from '@/api/master/productMaster'
import { getMaterialList } from '@/api/master/materialMaster'

export interface OptionItem {
  cd: string
  name: string
}

/** 顧客オプション（顧客マスタAPIを優先、未実装時は order API） */
export async function getCustomerOptions(): Promise<OptionItem[]> {
  try {
    const { getCustomerOptions: getMasterOptions } = await import('@/api/master/customerMaster')
    return await getMasterOptions()
  } catch {
    const list = await getCustomers()
    return (list || []).map((c) => ({
      cd: c.customer_code,
      name: c.customer_name || c.customer_code,
    }))
  }
}

export async function getProductOptions(): Promise<OptionItem[]> {
  const list = await getProducts()
  return (list || []).map((p) => ({
    cd: p.product_code,
    name: p.product_name || p.product_code,
  }))
}

export async function getDestinationOptions(customerCode?: string): Promise<OptionItem[]> {
  try {
    const list = await getDestinations(customerCode)
    const arr = (list || []).map((d) => ({
      cd: d.destination_code,
      name: d.destination_name || d.destination_code,
    }))
    return arr.sort((a, b) => (a.name || '').localeCompare(b.name || '', 'ja'))
  } catch {
    return []
  }
}

/** 納入先マスタからオプション取得（納入先休日画面など） */
export async function getDestinationMasterOptions(): Promise<OptionItem[]> {
  try {
    const { getDestinationOptions: getOptions } = await import('@/api/master/destinationMaster')
    return await getOptions()
  } catch {
    return []
  }
}

/** 運送会社オプション（未実装時は空） */
export async function getCarrierOptions(): Promise<OptionItem[]> {
  try {
    // 将来 carrier マスタがあればここで取得
    return []
  } catch {
    return []
  }
}

/** 製品マスタから製品CDオプション（製品一覧用） */
export async function getProductMasterOptions(): Promise<OptionItem[]> {
  try {
    const res = await getProductList({ page: 1, pageSize: 5000 })
    const list = res?.data?.list ?? res?.list ?? []
    return list.map((p) => ({ cd: p.product_cd, name: p.product_name || p.product_cd }))
  } catch {
    return []
  }
}

/** 材料マスタオプション */
export async function getMaterialOptions(): Promise<OptionItem[]> {
  try {
    const res = await getMaterialList({ page: 1, pageSize: 5000 })
    const list = res?.data?.list ?? res?.list ?? []
    return list.map((m) => ({ cd: m.material_cd, name: m.material_name || m.material_cd }))
  } catch {
    return []
  }
}

/** 仕入先オプション（仕入先マスタから取得） */
export async function getSupplierOptions(): Promise<OptionItem[]> {
  try {
    const { getSupplierList } = await import('@/api/master/supplierMaster')
    const res = await getSupplierList({ page: 1, pageSize: 5000 })
    const list = res?.data?.list ?? res?.list ?? []
    return list.map((s) => ({ cd: s.supplier_cd, name: s.supplier_name || s.supplier_cd }))
  } catch {
    return []
  }
}

/** 工程オプション（工程マスタAPIがある場合はそこから取得、未実装時は空） */
export async function getProcessOptions(): Promise<OptionItem[]> {
  try {
    const mod = await import('@/api/master/processMaster').catch(() => null)
    if (!mod?.getProcessList) return []
    const res = await mod.getProcessList({ page: 1, pageSize: 5000 })
    const list = res?.data?.list ?? res?.list ?? []
    return list.map((p: { process_cd: string; process_name?: string }) => ({
      cd: p.process_cd,
      name: p.process_name || p.process_cd,
    }))
  } catch {
    return []
  }
}

/** 工程詳細（歩留・サイクル自動設定用。工程マスタ未実装時はデフォルト値） */
export async function getProcessDetails(processCd: string): Promise<{
  success: boolean
  data?: { process_name?: string; default_yield?: number; default_cycle_sec?: number }
}> {
  try {
    const mod = await import('@/api/master/processMaster').catch(() => null)
    if (!mod?.getProcessByIdOrCd) {
      return { success: true, data: { process_name: processCd, default_yield: 1, default_cycle_sec: 0 } }
    }
    const row = await mod.getProcessByIdOrCd(processCd)
    return {
      success: true,
      data: {
        process_name: row?.process_name ?? processCd,
        default_yield: row?.default_yield != null ? Number(row.default_yield) : 1,
        default_cycle_sec: row?.default_cycle_sec != null ? Number(row.default_cycle_sec) : 0,
      },
    }
  } catch {
    return { success: true, data: { process_name: processCd, default_yield: 1, default_cycle_sec: 0 } }
  }
}

/** 工程ルートオプション（製品マスタ等のルート選択用） */
export async function getRouteOptions(): Promise<OptionItem[]> {
  try {
    const { fetchRoutes } = await import('@/api/master/processRouterMaster')
    const res = await fetchRoutes('', 1, 5000)
    const list = res?.data?.list ?? res?.list ?? []
    return list.map((r: { route_cd: string; route_name?: string }) => ({
      cd: r.route_cd,
      name: r.route_name || r.route_cd,
    }))
  } catch {
    return []
  }
}

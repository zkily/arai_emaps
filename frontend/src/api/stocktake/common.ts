/**
 * 棚卸フォーム用：マスタ・ユーザー一覧の薄いアダプタ
 */
import { getProducts as getErpProducts } from '@/api/erp/optionsData'
import { getMaterialList } from '@/api/master/materialMaster'
import { getPartList } from '@/api/master/partMaster'
import { fetchProcesses } from '@/api/master/processMaster'
import { getUsers as fetchSystemUsers } from '@/api/system'
import type { ProcessItem } from '@/types/master'

export interface Product {
  product_cd: string
  product_name: string
}

export interface Component {
  component_cd: string
  component_name: string
}

export interface MaterialRow {
  material_cd: string
  material_name: string
}

// BatchInventoryEntryDialog.vue では `type Material` を参照しているため、
// 互換の型エイリアスを用意する。
export type Material = MaterialRow

export type Process = ProcessItem

export interface User {
  username: string
  name: string
}

function normalizeMaterialList(res: Awaited<ReturnType<typeof getMaterialList>>): Material[] {
  const list = (res as { list?: Material[]; data?: { list?: Material[] } })?.list
    ?? (res as { data?: { list?: Material[] } })?.data?.list
    ?? []
  return Array.isArray(list) ? list : []
}

function normalizeProcesses(res: Awaited<ReturnType<typeof fetchProcesses>>): ProcessItem[] {
  const list = (res as { list?: ProcessItem[] })?.list
    ?? (res as { data?: { list?: ProcessItem[] } })?.data?.list
    ?? []
  return Array.isArray(list) ? list : []
}

export async function getProducts(): Promise<Product[]> {
  const rows = await getErpProducts()
  return (rows || []).map((p) => ({
    product_cd: p.product_code || (p as { product_cd?: string }).product_cd || '',
    product_name: p.product_name || '',
  }))
}

export async function getMaterials(): Promise<MaterialRow[]> {
  const res = await getMaterialList({ page: 1, pageSize: 5000 })
  return normalizeMaterialList(res).map((m) => ({
    material_cd: m.material_cd,
    material_name: m.material_name,
  }))
}

/** 棚卸フォーム用：parts を component_cd / component_name 形で返す（在庫ログの product_cd と一致） */
export async function getComponents(): Promise<Component[]> {
  try {
    const res = await getPartList({ page: 1, pageSize: 10000 })
    const list = res?.data?.list ?? []
    return list.map((p) => ({
      component_cd: p.part_cd,
      component_name: p.part_name,
    }))
  } catch {
    return []
  }
}

export async function getProcesses(): Promise<ProcessItem[]> {
  const res = await fetchProcesses({ page: 1, pageSize: 5000 })
  return normalizeProcesses(res)
}

/** システムユーザー一覧 API は page_size 最大 100（超えると 422） */
const SYSTEM_USERS_PAGE_SIZE_MAX = 100

export async function getUsers(): Promise<User[]> {
  const out: User[] = []
  let page = 1
  while (true) {
    const res = (await fetchSystemUsers({ page, page_size: SYSTEM_USERS_PAGE_SIZE_MAX })) as any
    const items = res?.items ?? res?.data?.items ?? []
    for (const u of items) {
      out.push({
        username: u.username,
        name: u.full_name || u.username,
      })
    }
    const total = Number(res?.total ?? res?.data?.total ?? 0)
    if (out.length >= total || items.length < SYSTEM_USERS_PAGE_SIZE_MAX) break
    page += 1
  }
  return out
}

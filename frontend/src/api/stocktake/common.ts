/**
 * 棚卸フォーム用：マスタ・ユーザー一覧の薄いアダプタ
 */
import { getProducts as getErpProducts } from '@/api/erp/optionsData'
import { getMaterialList } from '@/api/master/materialMaster'
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

/** 部品マスタ API 未整備のため空配列（必要になれば差し替え） */
export async function getComponents(): Promise<Component[]> {
  return []
}

export async function getProcesses(): Promise<ProcessItem[]> {
  const res = await fetchProcesses({ page: 1, pageSize: 5000 })
  return normalizeProcesses(res)
}

export async function getUsers(): Promise<User[]> {
  const res = (await fetchSystemUsers({ page: 1, page_size: 500 })) as any
  const items = res?.items ?? res?.data?.items ?? []
  return items.map((u: any) => ({
    username: u.username,
    name: u.full_name || u.username,
  }))
}

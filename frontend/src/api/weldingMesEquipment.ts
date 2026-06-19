import { fetchEquipmentEfficiencyProducts } from '@/api/aps'
import { getMachineList, type MachineItem } from '@/api/master/machineMaster'

export interface WeldingMesMachine {
  id: number
  machine_cd: string
  machine_name: string
}

/** 溶接 MES 製品下拉（equipment_efficiency：machines_name = 選択設備） */
export interface WeldingMesProductOption {
  product_code: string
  product_name: string
  unit_per_box?: number
}

export async function fetchWeldingMesProducts(machineId: number): Promise<WeldingMesProductOption[]> {
  const rows = await fetchEquipmentEfficiencyProducts(machineId)
  const seen = new Set<string>()
  const out: WeldingMesProductOption[] = []
  for (const r of rows ?? []) {
    const product_code = (r.product_cd ?? '').trim()
    if (!product_code || seen.has(product_code)) continue
    seen.add(product_code)
    const product_name = (r.product_name ?? '').trim() || product_code
    out.push({ product_code, product_name })
  }
  return out.sort((a, b) =>
    a.product_name.localeCompare(b.product_name, 'ja', { sensitivity: 'base' }),
  )
}

/** 溶接設備名：「溶接」+ 2 文字（例：溶接01、溶接SP） */
export const WELDING_MES_MACHINE_NAME_RE = /^溶接.{2}$/

export function isWeldingMesMachineLabel(label: string): boolean {
  return WELDING_MES_MACHINE_NAME_RE.test((label ?? '').trim())
}

function pickWeldingMesMachineLabel(row: MachineItem): string {
  const name = String(row.machine_name ?? '').trim()
  if (isWeldingMesMachineLabel(name)) return name
  const cd = String(row.machine_cd ?? '').trim()
  if (isWeldingMesMachineLabel(cd)) return cd
  return ''
}

/** 溶接設備一覧（設備マスタ・名称が「溶接」+2 文字のもののみ） */
export async function fetchWeldingMesMachines(): Promise<WeldingMesMachine[]> {
  const result = await getMachineList({ keyword: '溶接', pageSize: 500 })
  const list: MachineItem[] = result.data?.list ?? result.list ?? []
  return list
    .map((r) => {
      const label = pickWeldingMesMachineLabel(r)
      if (!label) return null
      return {
        id: Number(r.id),
        machine_cd: String(r.machine_cd ?? ''),
        machine_name: label,
      }
    })
    .filter((m): m is WeldingMesMachine => m != null && Number.isFinite(m.id) && m.id > 0)
    .sort((a, b) =>
      a.machine_name.localeCompare(b.machine_name, 'ja', { sensitivity: 'base' }),
    )
}

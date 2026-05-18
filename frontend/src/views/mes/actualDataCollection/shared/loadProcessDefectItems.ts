/**
 * 収集工程に紐づく不良項目をマスタから読み込む（MES 実績収集共通）
 */
import type { Composer } from 'vue-i18n'
import {
  fetchProcessDefectItemOptions,
  type ProcessDefectItem,
} from '@/api/master/processDefectItemMaster'

const MES_DEFECT_I18N_NS = 'mesInspectionActual'

/** 旧ハードコード不良 id → i18n キー（defectAppearance 等） */
const LEGACY_DEFECT_I18N_KEY: Record<string, string> = {
  appearance: 'defectAppearance',
  dimension: 'defectDimension',
  scratch: 'defectScratch',
  deformation: 'defectDeformation',
  stain: 'defectStain',
  foreign: 'defectForeign',
  color: 'defectColor',
  other: 'defectOther',
}

/** 不良項目表示名（言語切替：defectItems.{defect_cd} → 旧キー → マスタ名称） */
export function resolveMesDefectItemLabel(
  defectCd: string,
  fallbackName: string,
  t: Composer['t'],
  te: Composer['te'],
  i18nNs: string = MES_DEFECT_I18N_NS,
): string {
  const cd = (defectCd ?? '').trim()
  if (!cd) return fallbackName

  const itemKey = `${i18nNs}.defectItems.${cd}`
  if (te(itemKey)) return String(t(itemKey))

  const legacy =
    LEGACY_DEFECT_I18N_KEY[cd] ?? LEGACY_DEFECT_I18N_KEY[cd.toLowerCase()]
  if (legacy) {
    const legacyKey = `${i18nNs}.${legacy}`
    if (te(legacyKey)) return String(t(legacyKey))
  }

  return (fallbackName ?? '').trim() || cd
}

export interface MesDefectItemOption {
  id: string
  label: string
  attributableProcessCd: string
  attributableProcessName?: string
}

export async function loadMesDefectItemsForProcess(
  detectionProcessCd: string,
  attributableProcessCd?: string
): Promise<MesDefectItemOption[]> {
  const res = await fetchProcessDefectItemOptions(detectionProcessCd, attributableProcessCd)
  const list = res.data ?? []
  return list.map((row: ProcessDefectItem) => ({
    id: row.defect_cd,
    label: row.defect_name,
    attributableProcessCd: row.attributable_process_cd,
    attributableProcessName: row.attributable_process_name,
  }))
}

export function emptyDefectCountsFromItems(items: MesDefectItemOption[]): Record<string, number> {
  const out: Record<string, number> = {}
  for (const item of items) {
    out[item.id] = 0
  }
  return out
}

export function totalDefectCountFromItems(
  items: MesDefectItemOption[],
  defects: Record<string, number>
): number {
  return items.reduce((sum, d) => sum + Math.max(0, Math.round(defects[d.id] ?? 0)), 0)
}

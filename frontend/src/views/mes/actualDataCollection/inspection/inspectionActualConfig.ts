/** 検査工程 MES 実績収集：不良項目（マスタ連携前の既定一覧） */

export interface InspectionDefectItemDef {
  id: string
  /** i18n key under mesInspectionActual */
  labelKey: string
}

export const INSPECTION_DEFECT_ITEMS: InspectionDefectItemDef[] = [
  { id: 'appearance', labelKey: 'defectAppearance' },
  { id: 'dimension', labelKey: 'defectDimension' },
  { id: 'scratch', labelKey: 'defectScratch' },
  { id: 'deformation', labelKey: 'defectDeformation' },
  { id: 'stain', labelKey: 'defectStain' },
  { id: 'foreign', labelKey: 'defectForeign' },
  { id: 'color', labelKey: 'defectColor' },
  { id: 'other', labelKey: 'defectOther' },
]

export function emptyDefectCounts(): Record<string, number> {
  const out: Record<string, number> = {}
  for (const item of INSPECTION_DEFECT_ITEMS) {
    out[item.id] = 0
  }
  return out
}

export function totalDefectCount(defects: Record<string, number>): number {
  return INSPECTION_DEFECT_ITEMS.reduce((sum, d) => sum + Math.max(0, Math.round(defects[d.id] ?? 0)), 0)
}

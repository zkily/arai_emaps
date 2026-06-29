/** 成型計画試算 — 工程 key / 表示名 / 色 */
export const FORMING_PLAN_PROCESS_OPTIONS = [
  { key: 'cutting', label: '切断', color: '#5470c6' },
  { key: 'chamfering', label: '面取', color: '#91cc75' },
  { key: 'molding', label: '成型', color: '#fac858' },
  { key: 'plating', label: '社内メッキ', color: '#ee6666' },
  { key: 'outsourced_plating', label: '外注メッキ', color: '#fc8452' },
  { key: 'welding', label: '社内溶接', color: '#73c0de' },
  { key: 'outsourced_welding', label: '外注溶接', color: '#5470c6' },
  { key: 'inspection', label: '検査', color: '#3ba272' },
  { key: 'outsourced_warehouse', label: '外注検査', color: '#b37feb' },
  { key: 'warehouse', label: '倉庫', color: '#9a60b4' },
] as const

export type FormingPlanProcessKey = (typeof FORMING_PLAN_PROCESS_OPTIONS)[number]['key']

export const FORMING_PLAN_LOCALE = 'ja-JP'

export function fmtFormingNumber(v?: number | null, emptyZero = true): string {
  const n = Number(v ?? 0)
  if (!Number.isFinite(n)) return ''
  if (emptyZero && n === 0) return ''
  return n.toLocaleString(FORMING_PLAN_LOCALE)
}

export function processLabel(key: string) {
  return FORMING_PLAN_PROCESS_OPTIONS.find((o) => o.key === key)?.label ?? key
}

export function processColor(key: string) {
  return FORMING_PLAN_PROCESS_OPTIONS.find((o) => o.key === key)?.color ?? '#666'
}

/** 工程カード背景（淡色） */
export function processBgTint(key: string): string {
  const map: Record<string, string> = {
    cutting: 'linear-gradient(135deg, #eef2ff 0%, #f8faff 100%)',
    chamfering: 'linear-gradient(135deg, #ecfdf5 0%, #f6fffb 100%)',
    molding: 'linear-gradient(135deg, #fffbeb 0%, #fffdf5 100%)',
    plating: 'linear-gradient(135deg, #fef2f2 0%, #fff8f8 100%)',
    outsourced_plating: 'linear-gradient(135deg, #fff7ed 0%, #fffcf8 100%)',
    welding: 'linear-gradient(135deg, #ecfeff 0%, #f6feff 100%)',
    outsourced_welding: 'linear-gradient(135deg, #eff6ff 0%, #f8fbff 100%)',
    inspection: 'linear-gradient(135deg, #f0fdf4 0%, #f8fff9 100%)',
    outsourced_warehouse: 'linear-gradient(135deg, #faf5ff 0%, #fdfaff 100%)',
    warehouse: 'linear-gradient(135deg, #f5f3ff 0%, #faf9ff 100%)',
  }
  return map[key] ?? 'linear-gradient(135deg, #f8fafc 0%, #ffffff 100%)'
}

export function isMoldingReadonly(key: string) {
  return key === 'molding'
}

export const SOURCE_LABELS: Record<string, string> = {
  order_monthly: '月次受注',
  historical_avg: '履歴平均',
  pattern_only: 'パターン予測',
}

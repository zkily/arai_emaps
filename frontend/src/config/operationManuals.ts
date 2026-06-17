/**
 * マニュアル（トップレベルメニュー・マスタ管理と同級）
 * - MD・画像: frontend/src/views/manual/docs/ , frontend/src/views/manual/images/
 * - 画面: frontend/src/views/manual/ManualViewer.vue
 */

/** ManualHome 左サイドバーの分類 */
export type OperationManualCategory = 'planning' | 'instructionActual' | 'mes' | 'pageOperation'

export interface OperationManualEntry {
  /** URL スラッグ（/operation-manuals/:slug） */
  slug: string
  /** メニュー権限・i18n キー（menu.OP_MANUAL_*） */
  menuCode: string
  /** 画面ヘッダー主タイトル */
  pageTitle: string
  /** MD 相対パス（docs/ からの相対、例: forming-instruction_ja.md） */
  docFile: string
  /** 全体の表示順（未分類時のフォールバック） */
  sortOrder: number
  /** サイドバー分類 */
  category: OperationManualCategory
}

/** 分類の表示順（ManualHome 左メニュー） */
export const OPERATION_MANUAL_CATEGORY_ORDER: OperationManualCategory[] = [
  'planning',
  'instructionActual',
  'mes',
  'pageOperation',
]

export const OPERATION_MANUAL_CATEGORY_I18N_KEY: Record<OperationManualCategory, string> = {
  planning: 'operationManual.categoryPlanning',
  instructionActual: 'operationManual.categoryInstructionActual',
  mes: 'operationManual.categoryMes',
  pageOperation: 'operationManual.categoryPageOperation',
}

export const OPERATION_MANUAL_PARENT_CODE = 'OPERATION_MANUALS'

export const OPERATION_MANUAL_ROUTE_PREFIX = '/operation-manuals'

export const OPERATION_MANUALS: OperationManualEntry[] = [
  {
    slug: 'forming-planning',
    menuCode: 'OP_MANUAL_FORMING_PLANNING',
    pageTitle: '成型工程 計画作成',
    docFile: 'forming-planning_ja.md',
    sortOrder: 1,
    category: 'planning',
  },
  {
    slug: 'welding-planning',
    menuCode: 'OP_MANUAL_WELDING_PLANNING',
    pageTitle: '溶接工程 計画作成',
    docFile: 'welding-planning_ja.md',
    sortOrder: 2,
    category: 'planning',
  },
  {
    slug: 'plan-baseline',
    menuCode: 'OP_MANUAL_PLAN_BASELINE',
    pageTitle: '生産計画ベースライン管理',
    docFile: 'plan-baseline_ja.md',
    sortOrder: 5,
    category: 'pageOperation',
  },
  {
    slug: 'forming-instruction',
    menuCode: 'OP_MANUAL_FORMING',
    pageTitle: '成型工程 生産指示・実績収集',
    docFile: 'forming-instruction_ja.md',
    sortOrder: 4,
    category: 'instructionActual',
  },
  {
    slug: 'welding-instruction',
    menuCode: 'OP_MANUAL_WELDING',
    pageTitle: '溶接工程 生産指示・実績収集',
    docFile: 'welding-instruction_ja.md',
    sortOrder: 5,
    category: 'instructionActual',
  },
  {
    slug: 'cutting-instruction',
    menuCode: 'OP_MANUAL_CUTTING',
    pageTitle: '切断面取 生産指示・実績収集',
    docFile: 'cutting-instruction_ja.md',
    sortOrder: 6,
    category: 'instructionActual',
  },
  {
    slug: 'inspection-actual',
    menuCode: 'OP_MANUAL_INSPECTION',
    pageTitle: '検査実績収集',
    docFile: 'inspection-actual_ja.md',
    sortOrder: 7,
    category: 'mes',
  },
  {
    slug: 'inspection-actual-registration',
    menuCode: 'OP_MANUAL_INSPECTION_REGISTRATION',
    pageTitle: '検査実績収集登録',
    docFile: 'inspection-actual-registration_ja.md',
    sortOrder: 8,
    category: 'mes',
  },
  {
    slug: 'inspection-monitor',
    menuCode: 'OP_MANUAL_INSPECTION_MONITOR',
    pageTitle: '検査モニタ',
    docFile: 'inspection-monitor_ja.md',
    sortOrder: 9,
    category: 'mes',
  },
  {
    slug: 'inspection-productivity',
    menuCode: 'OP_MANUAL_INSPECTION_PRODUCTIVITY',
    pageTitle: '検査工程 — 生産性分析',
    docFile: 'inspection-productivity_ja.md',
    sortOrder: 10,
    category: 'mes',
  },
]

export interface OperationManualNavGroup {
  category: OperationManualCategory
  items: OperationManualEntry[]
}

/** ManualHome 用：分類ごとにマニュアルをグループ化（空の分類は除外） */
export function getOperationManualNavGroups(): OperationManualNavGroup[] {
  return OPERATION_MANUAL_CATEGORY_ORDER.map((category) => ({
    category,
    items: OPERATION_MANUALS.filter((m) => m.category === category).sort(
      (a, b) => a.sortOrder - b.sortOrder,
    ),
  })).filter((g) => g.items.length > 0)
}

export function getOperationManualPath(slug: string): string {
  return `${OPERATION_MANUAL_ROUTE_PREFIX}/${slug}`
}

export function getOperationManualBySlug(slug: string): OperationManualEntry | undefined {
  return OPERATION_MANUALS.find((m) => m.slug === slug)
}

/** メニューから新規タブでマニュアルを開く（メインレイアウト外） */
export function openOperationManualInNewTab(slug: string): void {
  const path = getOperationManualPath(slug)
  window.open(path, '_blank', 'noopener,noreferrer')
}

export function isOperationManualPath(path: string): boolean {
  return path === OPERATION_MANUAL_ROUTE_PREFIX || path.startsWith(`${OPERATION_MANUAL_ROUTE_PREFIX}/`)
}

/** menuConfig.ts 用の子メニュー定義（親 OPERATION_MANUALS は別途定義） */
export function getOperationManualMenuChildren(): Array<{
  code: string
  name: string
  path: string
  parentCode: string
  sortOrder: number
}> {
  return OPERATION_MANUALS.map((m) => ({
    code: m.menuCode,
    name: m.pageTitle,
    path: getOperationManualPath(m.slug),
    parentCode: OPERATION_MANUAL_PARENT_CODE,
    sortOrder: m.sortOrder,
  }))
}

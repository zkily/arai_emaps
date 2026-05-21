/**
 * マニュアル（トップレベルメニュー・マスタ管理と同級）
 * - MD・画像: frontend/src/views/manual/docs/ , frontend/src/views/manual/images/
 * - 画面: frontend/src/views/manual/ManualViewer.vue
 */

export interface OperationManualEntry {
  /** URL スラッグ（/operation-manuals/:slug） */
  slug: string
  /** メニュー権限・i18n キー（menu.OP_MANUAL_*） */
  menuCode: string
  /** 画面ヘッダー主タイトル */
  pageTitle: string
  /** MD 相対パス（docs/ からの相対、例: forming-instruction_ja.md） */
  docFile: string
  sortOrder: number
}

export const OPERATION_MANUAL_PARENT_CODE = 'OPERATION_MANUALS'

export const OPERATION_MANUAL_ROUTE_PREFIX = '/operation-manuals'

export const OPERATION_MANUALS: OperationManualEntry[] = [
  {
    slug: 'forming-instruction',
    menuCode: 'OP_MANUAL_FORMING',
    pageTitle: '成型工程 生産指示・実績収集',
    docFile: 'forming-instruction_ja.md',
    sortOrder: 1,
  },
  {
    slug: 'cutting-instruction',
    menuCode: 'OP_MANUAL_CUTTING',
    pageTitle: '切断・面取指示管理',
    docFile: 'cutting-instruction_ja.md',
    sortOrder: 2,
  },
  {
    slug: 'plan-baseline',
    menuCode: 'OP_MANUAL_PLAN_BASELINE',
    pageTitle: '生産計画ベースライン管理',
    docFile: 'plan-baseline_ja.md',
    sortOrder: 3,
  },
  {
    slug: 'inspection-actual',
    menuCode: 'OP_MANUAL_INSPECTION',
    pageTitle: '検査実績収集',
    docFile: 'inspection-actual_ja.md',
    sortOrder: 4,
  },
]

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

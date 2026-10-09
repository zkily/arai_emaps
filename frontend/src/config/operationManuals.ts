/**
 * マニュアル（トップレベルメニュー・マスタ管理と同級）
 * - MD・画像: frontend/src/views/manual/docs/ , frontend/src/views/manual/images/
 * - 画面: frontend/src/views/manual/ManualViewer.vue
 */
import { menuConfig } from '@/router/menuConfig'

/** ManualHome 左サイドバーの分類 */
export type OperationManualCategory =
  | 'planning'
  | 'instructionActual'
  | 'mes'
  | 'pageOperation'

export interface OperationManualEntry {
  /** URL スラッグ（/operation-manuals/:slug） */
  slug: string
  /** メニュー権限・i18n キー（menu.OP_MANUAL_*） */
  menuCode: string
  /** 画面ヘッダー主タイトル */
  pageTitle: string
  /** MD 相対パス（docs/ からの相対、例: forming-instruction_ja.md）。PDF のときは省略 */
  docFile?: string
  /** pdfs/ 直下のファイル名（例: equipment-efficiency.pdf） */
  pdfFile?: string
  /** 全体の表示順（未分類時のフォールバック） */
  sortOrder: number
  /** サイドバー分類 */
  category: OperationManualCategory
  /**
   * 対象画面の menuConfig コード（例: MASTER_EQUIPMENT_EFFICIENCY）。
   * ツリー表示の分類（ページ操作関連）では、ページメニューと同じ親メニュー階層の下に配置される
   */
  pageMenuCode?: string
}

/** ページメニューと同じ階層で開閉表示する分類 */
export const OPERATION_MANUAL_TREE_CATEGORIES: OperationManualCategory[] = ['pageOperation']

/** 分類の表示順（ManualHome 左メニュー） */
export const OPERATION_MANUAL_CATEGORY_ORDER: OperationManualCategory[] = [
  'pageOperation',
  'planning',
  'instructionActual',
  'mes',
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
    slug: 'forming-setup-schedule',
    menuCode: 'OP_MANUAL_FORMING_SETUP',
    pageTitle: '成型生産計画段替予定表',
    pdfFile: 'forming-setup-schedule.pdf',
    sortOrder: 3,
    category: 'planning',
  },
  {
    slug: 'plan-baseline',
    menuCode: 'OP_MANUAL_PLAN_BASELINE',
    pageTitle: '生産計画ベースライン管理',
    pdfFile: 'plan-baseline.pdf',
    sortOrder: 5,
    category: 'pageOperation',
    pageMenuCode: 'ERP_PRODUCTION_BASELINE',
  },
  {
    slug: 'equipment-efficiency',
    menuCode: 'OP_MANUAL_EQUIPMENT_EFFICIENCY',
    pageTitle: '設備能率管理',
    pdfFile: 'equipment-efficiency.pdf',
    sortOrder: 12,
    category: 'pageOperation',
    pageMenuCode: 'MASTER_EQUIPMENT_EFFICIENCY',
  },
  {
    slug: 'main-screen',
    menuCode: 'OP_MANUAL_MAIN_SCREEN',
    pageTitle: 'メイン画面（ダッシュボード）',
    pdfFile: 'main-screen.pdf',
    sortOrder: 0,
    category: 'pageOperation',
    pageMenuCode: 'DASHBOARD',
  },
  {
    slug: 'order-monthly',
    menuCode: 'OP_MANUAL_ORDER_MONTHLY',
    pageTitle: '月受注管理',
    pdfFile: 'order-monthly.pdf',
    sortOrder: 13,
    category: 'pageOperation',
    pageMenuCode: 'ERP_ORDER_MONTHLY',
  },
  {
    slug: 'order-daily',
    menuCode: 'OP_MANUAL_ORDER_DAILY',
    pageTitle: '日受注管理',
    pdfFile: 'order-daily.pdf',
    sortOrder: 14,
    category: 'pageOperation',
    pageMenuCode: 'ERP_ORDER_DAILY',
  },
  {
    slug: 'supply-parts',
    menuCode: 'OP_MANUAL_SUPPLY_PARTS',
    pageTitle: '補給品管理',
    pdfFile: 'supply-parts.pdf',
    sortOrder: 15,
    category: 'pageOperation',
    pageMenuCode: 'ERP_INVENTORY_SUPPLY_PARTS',
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
    slug: 'inspection-actual-android',
    menuCode: 'OP_MANUAL_INSPECTION_ANDROID',
    pageTitle: '検査実績収集（Android）',
    docFile: 'inspection-actual-android_ja.md',
    sortOrder: 8,
    category: 'mes',
  },
  {
    slug: 'inspection-actual-registration',
    menuCode: 'OP_MANUAL_INSPECTION_REGISTRATION',
    pageTitle: '検査実績収集登録',
    docFile: 'inspection-actual-registration_ja.md',
    sortOrder: 9,
    category: 'mes',
  },
  {
    slug: 'inspection-monitor',
    menuCode: 'OP_MANUAL_INSPECTION_MONITOR',
    pageTitle: '検査モニタ',
    docFile: 'inspection-monitor_ja.md',
    sortOrder: 10,
    category: 'mes',
  },
  {
    slug: 'inspection-productivity',
    menuCode: 'OP_MANUAL_INSPECTION_PRODUCTIVITY',
    pageTitle: '検査工程 — 生産性分析',
    docFile: 'inspection-productivity_ja.md',
    sortOrder: 11,
    category: 'mes',
  },
  {
    slug: 'outsourcing-welding',
    menuCode: 'OP_MANUAL_OUTSOURCING_WELDING',
    pageTitle: '外注溶接',
    pdfFile: 'outsourcing-welding.pdf',
    sortOrder: 21,
    category: 'pageOperation',
    pageMenuCode: 'ERP_OUTSOURCING_WELDING_ORDER',
  },
  {
    slug: 'outsourcing-plating',
    menuCode: 'OP_MANUAL_OUTSOURCING_PLATING',
    pageTitle: '外注メッキ',
    pdfFile: 'outsourcing-plating.pdf',
    sortOrder: 20,
    category: 'pageOperation',
    pageMenuCode: 'ERP_OUTSOURCING_PLATING_ORDER',
  },
]

/** ManualHome ツリー表示用ノード（親メニュー＝フォルダ、マニュアル＝リーフ） */
export interface OperationManualTreeNode {
  /** フォルダ: menuConfig コード / リーフ: `manual:<slug>` */
  key: string
  /** フォルダのみ：menuConfig コード（i18n menu.<CODE>） */
  menuCode?: string
  name: string
  icon?: string
  sortOrder: number
  children: OperationManualTreeNode[]
  manual?: OperationManualEntry
}

export interface OperationManualNavGroup {
  category: OperationManualCategory
  items: OperationManualEntry[]
  /** OPERATION_MANUAL_TREE_CATEGORIES の分類のみ */
  tree?: OperationManualTreeNode[]
}

const menuConfigByCode = new Map(menuConfig.map((m) => [m.code, m]))

/** pageMenuCode の親メニューを上位から順に返す（対象画面自身は含まない） */
function getPageMenuAncestorCodes(pageMenuCode: string): string[] {
  const codes: string[] = []
  const visited = new Set<string>()
  let parentCode = menuConfigByCode.get(pageMenuCode)?.parentCode
  while (parentCode && !visited.has(parentCode)) {
    visited.add(parentCode)
    codes.unshift(parentCode)
    parentCode = menuConfigByCode.get(parentCode)?.parentCode
  }
  return codes
}

/** 同一階層はページメニューの sortOrder 順（同順位はマニュアルの sortOrder 順） */
function sortManualTree(nodes: OperationManualTreeNode[]): void {
  nodes.sort(
    (a, b) =>
      a.sortOrder - b.sortOrder ||
      (a.manual?.sortOrder ?? 0) - (b.manual?.sortOrder ?? 0),
  )
  nodes.forEach((n) => sortManualTree(n.children))
}

/** pageMenuCode を基に、ページメニューと同じ階層のツリーを組み立てる */
export function buildOperationManualMenuTree(
  items: OperationManualEntry[],
): OperationManualTreeNode[] {
  const roots: OperationManualTreeNode[] = []
  const folders = new Map<string, OperationManualTreeNode>()

  for (const manual of items) {
    let siblings = roots
    const ancestorCodes =
      manual.pageMenuCode && menuConfigByCode.has(manual.pageMenuCode)
        ? getPageMenuAncestorCodes(manual.pageMenuCode)
        : []
    for (const code of ancestorCodes) {
      let folder = folders.get(code)
      if (!folder) {
        const menu = menuConfigByCode.get(code)
        folder = {
          key: code,
          menuCode: code,
          name: menu?.name ?? code,
          icon: menu?.icon,
          sortOrder: menu?.sortOrder ?? 0,
          children: [],
        }
        folders.set(code, folder)
        siblings.push(folder)
      }
      siblings = folder.children
    }
    const leaf = toOperationManualLeafNode(manual)
    const pageMenu = manual.pageMenuCode ? menuConfigByCode.get(manual.pageMenuCode) : undefined
    if (pageMenu) leaf.sortOrder = pageMenu.sortOrder
    siblings.push(leaf)
  }

  sortManualTree(roots)
  return roots
}

export function toOperationManualLeafNode(manual: OperationManualEntry): OperationManualTreeNode {
  return {
    key: `manual:${manual.slug}`,
    name: manual.pageTitle,
    sortOrder: manual.sortOrder,
    children: [],
    manual,
  }
}

/** ManualHome 用：分類ごとにマニュアルをグループ化（空の分類は除外） */
export function getOperationManualNavGroups(): OperationManualNavGroup[] {
  return OPERATION_MANUAL_CATEGORY_ORDER.map((category) => {
    const items = OPERATION_MANUALS.filter((m) => m.category === category).sort(
      (a, b) => a.sortOrder - b.sortOrder,
    )
    const group: OperationManualNavGroup = { category, items }
    if (OPERATION_MANUAL_TREE_CATEGORIES.includes(category)) {
      group.tree = buildOperationManualMenuTree(items)
    }
    return group
  }).filter((g) => g.items.length > 0)
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

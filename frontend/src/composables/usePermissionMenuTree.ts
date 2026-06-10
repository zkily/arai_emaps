/**
 * 権限・ロール管理のメニューツリー構築。
 * サイドバーと同じ menuConfig 階層を使い、menus テーブルの code→id で DB 権限と紐付ける。
 */
import { menuConfig, type MenuConfigItem } from '@/router/menuConfig'
import { buildTree, type MenuTreeNode as ConfigMenuNode } from '@/composables/useMenuTree'

export interface PermissionMenuTreeNode {
  id: number
  code: string
  label: string
  children: PermissionMenuTreeNode[]
}

/** SidebarMenu.vue と同じルート（DASHBOARD は別扱い） */
const ROOT_MENU_CODES = ['ERP', 'APS', 'MES', 'FIN', 'MASTER', 'SYSTEM'] as const

function attachPermissionIds(
  node: ConfigMenuNode,
  codeToId: Map<string, number>,
): PermissionMenuTreeNode[] {
  const id = codeToId.get(node.code)
  const children = node.children.flatMap((c) => attachPermissionIds(c, codeToId))
  if (id == null && children.length === 0) return []
  if (id == null) return children
  return [{ id, code: node.code, label: node.name, children }]
}

/** menuConfig + code→id から権限設定用ツリーを構築（DB の孤立・重複ノードは含めない） */
export function buildPermissionMenuTree(codeToId: Map<string, number>): PermissionMenuTreeNode[] {
  const result: PermissionMenuTreeNode[] = []
  const dashId = codeToId.get('DASHBOARD')
  const dashItem = (menuConfig as MenuConfigItem[]).find((m) => m.code === 'DASHBOARD')
  if (dashId != null && dashItem) {
    result.push({ id: dashId, code: 'DASHBOARD', label: dashItem.name, children: [] })
  }
  for (const code of ROOT_MENU_CODES) {
    const root = buildTree(code)
    if (root) result.push(...attachPermissionIds(root, codeToId))
  }
  return result
}

function collectDescendantCodes(node: PermissionMenuTreeNode): Set<string> {
  const codes = new Set<string>()
  const walk = (n: PermissionMenuTreeNode) => {
    codes.add(n.code)
    n.children.forEach(walk)
  }
  walk(node)
  return codes
}

/** 子が全て揃っていない親 code は UI 表示から除外 */
export function pruneParentCodesUnlessFullySelected(
  tree: PermissionMenuTreeNode[],
  codes: Set<string>,
): Set<string> {
  const result = new Set(codes)
  const visit = (node: PermissionMenuTreeNode) => {
    node.children.forEach(visit)
    if (node.children.length === 0 || !result.has(node.code)) return
    const descendants = [...collectDescendantCodes(node)].filter((c) => c !== node.code)
    if (descendants.length > 0 && !descendants.every((c) => result.has(c))) {
      result.delete(node.code)
    }
  }
  tree.forEach(visit)
  return result
}

export function collectPermissionTreeIds(tree: PermissionMenuTreeNode[]): Set<number> {
  const ids = new Set<number>()
  const walk = (nodes: PermissionMenuTreeNode[]) => {
    for (const n of nodes) {
      ids.add(n.id)
      walk(n.children)
    }
  }
  walk(tree)
  return ids
}

/** DB の menu_permissions をツリー上の default-checked-keys 用に正規化 */
export function menuIdsToTreeCheckedKeys(
  menuIds: number[],
  tree: PermissionMenuTreeNode[],
): number[] {
  const idToCode = new Map<number, string>()
  const codeToId = new Map<string, number>()
  const walk = (nodes: PermissionMenuTreeNode[]) => {
    for (const n of nodes) {
      idToCode.set(n.id, n.code)
      codeToId.set(n.code, n.id)
      walk(n.children)
    }
  }
  walk(tree)
  const codes = new Set(
    menuIds.map((id) => idToCode.get(id)).filter((c): c is string => c != null),
  )
  const pruned = pruneParentCodesUnlessFullySelected(tree, codes)
  return [...pruned].map((code) => codeToId.get(code)!).filter((id) => id != null)
}

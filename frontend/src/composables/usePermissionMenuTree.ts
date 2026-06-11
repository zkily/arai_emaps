/**
 * 権限・ロール管理のメニューツリー構築。
 * SidebarMenu と同じ menuConfig 階層・ルート順を使い、menus テーブルの code→id で DB 権限と紐付ける。
 */
import { menuConfig, type MenuConfigItem } from '@/router/menuConfig'
import { SIDEBAR_ROOT_MENU_CODES } from '@/config/sidebarMenu'
import { buildTree, type MenuTreeNode as ConfigMenuNode } from '@/composables/useMenuTree'

export interface PermissionMenuTreeNode {
  id: number
  code: string
  label: string
  icon?: string
  /** menus テーブルに未登録（ルート定義から取り込みが必要） */
  syncMissing?: boolean
  disabled?: boolean
  children: PermissionMenuTreeNode[]
}

function attachPermissionIds(
  node: ConfigMenuNode,
  codeToId: Map<string, number>,
): PermissionMenuTreeNode {
  const id = codeToId.get(node.code)
  const syncMissing = id == null
  return {
    id: id ?? 0,
    code: node.code,
    label: node.name,
    icon: node.icon,
    syncMissing,
    disabled: syncMissing,
    children: node.children.map((c) => attachPermissionIds(c, codeToId)),
  }
}

/** menuConfig + code→id から権限設定用ツリーを構築（SidebarMenu と同じ構造を常に保持） */
export function buildPermissionMenuTree(codeToId: Map<string, number>): PermissionMenuTreeNode[] {
  const result: PermissionMenuTreeNode[] = []
  const dashItem = (menuConfig as MenuConfigItem[]).find((m) => m.code === 'DASHBOARD')
  const dashId = codeToId.get('DASHBOARD')
  if (dashItem) {
    const syncMissing = dashId == null
    result.push({
      id: dashId ?? 0,
      code: 'DASHBOARD',
      label: dashItem.name,
      icon: dashItem.icon,
      syncMissing,
      disabled: syncMissing,
      children: [],
    })
  }
  for (const code of SIDEBAR_ROOT_MENU_CODES) {
    const root = buildTree(code)
    if (root) result.push(attachPermissionIds(root, codeToId))
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

/** 親メニューが選択されている場合、配下の選択可能な子 code も含める（保存用） */
export function expandCheckedCodesWithDescendants(
  tree: PermissionMenuTreeNode[],
  codes: Iterable<string>,
): string[] {
  const codeSet = new Set(codes)
  const nodeByCode = new Map<string, PermissionMenuTreeNode>()
  const walk = (nodes: PermissionMenuTreeNode[]) => {
    for (const n of nodes) {
      nodeByCode.set(n.code, n)
      walk(n.children)
    }
  }
  walk(tree)

  const addCheckableDescendants = (node: PermissionMenuTreeNode) => {
    for (const child of node.children) {
      if (!child.disabled) codeSet.add(child.code)
      addCheckableDescendants(child)
    }
  }

  for (const code of [...codeSet]) {
    const node = nodeByCode.get(code)
    if (node?.children.length) addCheckableDescendants(node)
  }
  return [...codeSet]
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

export function collectPermissionTreeCodeToId(tree: PermissionMenuTreeNode[]): Map<string, number> {
  const map = new Map<string, number>()
  const walk = (nodes: PermissionMenuTreeNode[]) => {
    for (const n of nodes) {
      if (n.id > 0) map.set(n.code, n.id)
      walk(n.children)
    }
  }
  walk(tree)
  return map
}

/** DB の menu_permissions をツリー上の default-checked-keys（code）用に正規化 */
export function menuIdsToTreeCheckedKeys(
  menuIds: number[],
  tree: PermissionMenuTreeNode[],
): string[] {
  const idToCode = new Map<number, string>()
  const walk = (nodes: PermissionMenuTreeNode[]) => {
    for (const n of nodes) {
      if (n.id > 0) idToCode.set(n.id, n.code)
      walk(n.children)
    }
  }
  walk(tree)
  const codes = new Set(
    menuIds.map((id) => idToCode.get(id)).filter((c): c is string => c != null),
  )
  return [...pruneParentCodesUnlessFullySelected(tree, codes)]
}

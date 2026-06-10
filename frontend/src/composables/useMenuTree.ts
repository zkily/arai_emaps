/**
 * menuConfig（単一ソース）から指定ルートコード配下のメニューツリーを構築する。
 * SidebarMenu の FIN セクションは、手書きの el-menu-item ではなく本ツリーを
 * MenuTreeItem.vue で再帰描画する（メニュー定義の二重管理を解消）。
 */
import { menuConfig, type MenuConfigItem } from '@/router/menuConfig'

export interface MenuTreeNode {
  code: string
  name: string
  path?: string
  icon?: string
  sortOrder: number
  children: MenuTreeNode[]
}

function buildTree(rootCode: string): MenuTreeNode | null {
  const byCode = new Map<string, MenuTreeNode>()
  for (const item of menuConfig as MenuConfigItem[]) {
    byCode.set(item.code, {
      code: item.code,
      name: item.name,
      path: item.path,
      icon: item.icon,
      sortOrder: item.sortOrder,
      children: [],
    })
  }
  for (const item of menuConfig as MenuConfigItem[]) {
    if (item.parentCode && byCode.has(item.parentCode)) {
      byCode.get(item.parentCode)!.children.push(byCode.get(item.code)!)
    }
  }
  const sortRec = (node: MenuTreeNode) => {
    node.children.sort((a, b) => a.sortOrder - b.sortOrder)
    node.children.forEach(sortRec)
  }
  const root = byCode.get(rootCode) || null
  if (root) sortRec(root)
  return root
}

/** ルートコード（例: 'FIN'）配下のメニューツリーを返す。 */
export function useMenuTree(rootCode: string): MenuTreeNode | null {
  return buildTree(rootCode)
}

export { buildTree }
